"""Selected video entries keep UI routing, phase ownership and model isolation."""
import ast
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import shlex
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

class VideoEntryTests(unittest.TestCase):
    def test_entries_use_tested_engines_and_dimensions(self):
        entries=json.loads((ROOT/'config/comfy-video-entries.json').read_text())
        self.assertEqual(entries['defaults'],dict(width=512,height=288,frames=33,CPU_weight_offload=False))
        rows={r['id']:r for r in entries['models']}
        self.assertEqual(rows['wan22-5b']['render_stage'],'baseline')
        self.assertEqual(rows['ltx23-mesh']['render_stage'],'mesh')
        for row in rows.values():
            for key in ('workflow','api_workflow'):self.assertTrue((ROOT/row[key]).is_file())
    def test_canvas_and_api_route_through_selected_entry(self):
        entries=load('video_entries_test','scripts/comfy_video_entries.py')
        for name in ('wan22-5b','ltx23-mesh'):
            graph=entries.graph(name,123,'New caption')
            self.assertEqual(graph['1']['inputs'],dict(entry=name,seed=123,prompt='New caption',resolution='512x288'))
            canvas=json.loads((ROOT/f'config/comfy-workflows/{name}.json').read_text())
            self.assertEqual(canvas['nodes'][0]['widgets_values'][0],name)
    def test_video_shortcuts_are_foreground_guarded_servers(self):
        installer=load('comfy_shortcut_test','scripts/install_comfy_shortcut.py')
        text=installer.content('Video','wan22-5b',True)
        self.assertIn('Terminal=true',text);self.assertIn('--video-entry --serve --foreground-backend',text)
        self.assertIn('visible_terminal.py',text)
    def test_all_resolution_presets_reach_the_qualified_render_graph(self):
        entries=load('video_resolution_test','scripts/comfy_video_entries.py')
        trial=load('video_resolution_graph','scripts/comfy_video_trial.py')
        for name,stage in [('wan22-5b','baseline'),('ltx23-mesh','mesh')]:
            for resolution,(width,height) in entries.RESOLUTIONS.items():
                request=entries.graph(name,resolution=resolution)['1']['inputs']
                self.assertEqual(request['resolution'],resolution)
                graph=trial.graph(stage,request['seed'],*entries.dimensions(request['resolution']))
                self.assertEqual(graph['4']['inputs']['height'],(height+31)//32*32)
                self.assertEqual(graph['4']['inputs']['width'],width)
                if resolution!='512x288':
                    self.assertEqual(graph['23']['inputs']['height'],height)
                    filename=name+'-'+resolution
                    canvas=json.loads((ROOT/f'config/comfy-workflows/{filename}.json').read_text())
                    self.assertEqual(canvas['nodes'][0]['widgets_values'][-1],resolution)
                    api=json.loads((ROOT/f'config/comfy-workflows/{filename}.api.json').read_text())
                    self.assertEqual(api['1']['inputs']['resolution'],resolution)
                if name=='wan22-5b' and resolution=='1080p':self.assertEqual(graph['1']['class_type'],'NvidiaWanSplitDenoiser')
        for bad in ('4K','1080','1920x1080',None):
            with self.assertRaises(AssertionError):entries.dimensions(bad)

    def test_desktop_hd_actions_keep_entry_guards_and_model(self):
        installer=load('video_actions_test','scripts/install_comfy_shortcut.py')
        for name in ('wan22-5b','ltx23-mesh'):
            text=installer.content('Video',name,True)
            for resolution in ('720p','1080p'):
                section=text.split('[Desktop Action '+resolution+']')[1].split('[Desktop Action ')[0]
                command=shlex.split(next(line[5:] for line in section.splitlines() if line.startswith('Exec=')))
                self.assertEqual(command[command.index('--model')+1],name)
                self.assertEqual(command[command.index('--video-resolution')+1],resolution)
                for flag in ('--video-entry','--serve','--foreground-backend'):self.assertIn(flag,command)

    def test_new_presets_install_without_overwriting_saved_workflows(self):
        entries=load('video_preset_install','scripts/comfy_video_entries.py')
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary);existing=folder/'wan22-5b.json';existing.write_text('custom saved workflow')
            entries.install_workflows('wan22-5b',folder)
            self.assertEqual(existing.read_text(),'custom saved workflow')
            self.assertEqual(json.loads((folder/'wan22-5b-1080p.json').read_text())['nodes'][0]['widgets_values'][-1],'1080p')
            hd=folder/'wan22-5b-720p.json';hd.write_text('custom HD workflow');entries.install_workflows('wan22-5b',folder)
            self.assertEqual(hd.read_text(),'custom HD workflow')

    def test_image_shortcut_content_remains_identical(self):
        installer=load('comfy_shortcut_image_test','scripts/install_comfy_shortcut.py')
        path=Path.home()/'Desktop/ComfyUI Qwen Turbo.desktop'
        if not path.exists():self.skipTest('Desktop shortcuts are installed only on the maintained host')
        # Public checkout tests may run beside the installed private checkout.
        installed=path.read_text();installer.ROOT=Path(next(line[5:] for line in installed.splitlines() if line.startswith('Path=')))
        self.assertEqual(installed,installer.content('ComfyUI Qwen Turbo','qwen-image-2.1-turbo'))
    def test_ui_rejects_direct_gpu_loader_bypass(self):
        tree=ast.parse((ROOT/'scripts/comfy_video_nodes/__init__.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='file')
        namespace=dict(os=os);exec(compile(ast.Module(body=[node],type_ignores=[]),'entry_gate','exec'),namespace)
        with patch.dict(os.environ,COMFY_VIDEO_ENTRY='wan22-5b',COMFY_VIDEO_ENTRY_CHILD=''):
            with self.assertRaisesRegex(AssertionError,'selected video'):namespace['file']('unused')
    def test_phase_cleanup_only_terminates_the_owned_process(self):
        sys.path.insert(0,str(ROOT/'scripts'))
        try:job=load('comfy_video_job_test','scripts/comfy_video_job.py')
        finally:sys.path.pop(0)
        calls=[]
        child=SimpleNamespace(poll=lambda:None,terminate=lambda:calls.append('terminate'),wait=lambda timeout:calls.append(('wait',timeout)))
        job.stop(child);self.assertEqual(calls,['terminate',('wait',10)])
    def test_phase_cleanup_escalates_only_after_owned_timeout(self):
        sys.path.insert(0,str(ROOT/'scripts'))
        try:job=load('comfy_video_job_timeout_test','scripts/comfy_video_job.py')
        finally:sys.path.pop(0)
        calls=[]
        def wait(timeout):
            calls.append(('wait',timeout))
            if timeout==10:raise subprocess.TimeoutExpired('owned',timeout)
        child=SimpleNamespace(poll=lambda:None,terminate=lambda:calls.append('terminate'),wait=wait,kill=lambda:calls.append('kill'))
        job.stop(child);self.assertEqual(calls,['terminate',('wait',10),'kill',('wait',5)])

class VideoPromptBudgetTests(unittest.TestCase):
    def test_ltx_prompt_cannot_expand_encoder_past_tested_padding(self):
        tree=ast.parse((ROOT/'scripts/comfy_video_nodes/__init__.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='require_bounded_ltx_tokens')
        namespace={};exec(compile(ast.Module(body=[node],type_ignores=[]),'prompt_budget','exec'),namespace)
        check=namespace['require_bounded_ltx_tokens'];check({'gemma':[[0]*256]})
        for tokens in ({'gemma':[[0]*257]},{'gemma':[[0]*128,[0]*128]},{}):
            with self.assertRaisesRegex(AssertionError,'256-token'):check(tokens)

class VideoJobGroupTests(unittest.TestCase):
    def test_crashed_leader_still_cleans_owned_descendant_group(self):
        entries=load('video_group_test','scripts/comfy_video_entries.py');calls=[]
        def killpg(pid,sig):
            calls.append((pid,sig))
            if sig==0:raise ProcessLookupError()
        process=SimpleNamespace(pid=123,wait=lambda timeout:calls.append(('wait',timeout)))
        with patch.object(entries.os,'killpg',side_effect=killpg):entries.stop_job_group(process)
        self.assertEqual(calls,[(123,entries.signal.SIGTERM),('wait',15),(123,0)])
