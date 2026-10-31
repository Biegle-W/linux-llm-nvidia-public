# Terminal attention and backend focus policy — October 31, 2026

The user clarified that terminals needing attention must come to the front; only backend consoles should default to minimized. This supersedes the earlier all-terminal minimization preference.

The shared launcher now omits native-iconic startup for harnesses, installation/authentication tasks and engine selectors. It restores and requests activation of the owned window, then verifies the window manager's active-window property. Backend monitor startup explicitly retains native-iconic mode and does not request focus. The pinned terminal runtime, ownership rules, resource guards and auto-close behavior are unchanged.

Three focused launcher tests passed. The actual ACS password terminal was opened with foreground activation confirmed by the window manager. No running backend was restarted or refocused.

The previous ACS audit had exited before any change because its work guard counted a ptyxis terminal on the motherboard-connected 3060. The guard now filters by the two target GPU UUIDs; four ACS safety tests passed, including exclusion of 3060 work. The retry is an attention task and opens in front. These UI/guard fixes do not establish P2P correctness; the actual scoped routing trial is still separately recorded.
