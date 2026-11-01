#!/usr/bin/env python3
"""Enforce background-window policy even for launchers already imported by services."""
from pathlib import Path
import hashlib,json,os,sys
ROOT=Path(__file__).resolve().parents[1]
def background(args):
 before=[];child=[]
 if '-e' in args:
  index=args.index('-e');before=args[:index];child=args[index+1:]
 else:before=args
 if '-iconic' in before:return True
 for index,value in enumerate(child[:-1]):
  if Path(value).name=='visible_terminal.py' and child[index+1]=='watch':return True
 return False

def main():
 if sys.argv[1:2]==['--background-child']:
  from visible_terminal import background_terminal
  background_terminal(os.environ.get('WINDOWID'))
  child=sys.argv[3:]
  if not child:raise SystemExit('Background terminal child is missing')
  os.execvpe(child[0],child,dict(os.environ))
  return
 config=json.loads((ROOT/'config/terminal-runtime.json').read_text());relative=config['native_binary'];binary=ROOT/relative
 if not binary.resolve().is_relative_to(ROOT.resolve()) or hashlib.sha256(binary.read_bytes()).hexdigest()!=config['sha256'][relative]:raise SystemExit('Native terminal verification failed')
 args=sys.argv[1:];env=dict(os.environ)
 if background(args):
  env.pop('DESKTOP_STARTUP_ID',None);env.pop('XDG_ACTIVATION_TOKEN',None)
  if '-e' not in args:raise SystemExit('Background terminal command is missing')
  index=args.index('-e');child=args[index+1:];args=args[:index+1]+['/usr/bin/python3',str(Path(__file__).resolve()),'--background-child','--',*child]
  args=['-iconic','-xrm','*input: false','-xrm','*popOnBell: false','-xrm','*bellIsUrgent: false','-xrm','*zIconBeep: 0','-xrm','*allowWindowOps: false',*args]
 os.execve(binary,[str(binary),*args],env)
if __name__=='__main__':main()
