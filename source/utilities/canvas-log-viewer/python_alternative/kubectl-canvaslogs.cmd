@echo off

if "%1" == "comp" (
	kubectl logs -n canvas deployment/component-operator | python showlogtree.py "%2"
	exit 0
)
if "%1" == "sman" (
	kubectl logs -n canvas deployment/canvas-smanop | python showlogtree.py "%2"
	exit 0
)
if "%1" == "depapi" (
	kubectl logs -n canvas deployment/canvas-depapi-op | python showlogtree.py "%2"
	exit 0
)
echo "usage: kubectl canvaslogs (comp|sman|depapi) [componentfilter]"
echo "       needs python with 'pip install rich'"
