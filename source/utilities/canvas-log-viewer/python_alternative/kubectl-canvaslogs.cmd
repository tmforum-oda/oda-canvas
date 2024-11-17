@echo off

if "%1" == "smanop" (
	kubectl logs -n canvas deployment/canvas-smanop | python showlogtree.py
	exit 0
)
if "%1" == "compop" (
	kubectl logs -n canvas deployment/component-operator | python showlogtree.py
	exit 0
)
if [%1] == [] (
	kubectl logs -n canvas deployment/component-operator | python showlogtree.py
	exit 0
)
echo "usage: kubectl canvaslogs [compop|smanop]"
echo "       needs python with 'pip install rich'"