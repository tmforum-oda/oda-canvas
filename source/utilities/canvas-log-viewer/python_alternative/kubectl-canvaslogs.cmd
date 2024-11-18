@echo off

if "%1" == "comp" (
	kubectl logs -n canvas deployment/component-operator -c component-operator | python showlogtree.py "%2"
	GOTO :eof
)
if "%1" == "sman" (
	kubectl logs -n canvas deployment/canvas-smanop | python showlogtree.py "%2"
	GOTO :eof
)
if "%1" == "depapi" (
	kubectl logs -n canvas deployment/canvas-depapi-op | python showlogtree.py "%2"
	GOTO :eof
)
if "%1" == "apiistio" (
	kubectl logs -n canvas deployment/api-operator-istio | python showlogtree.py "%2"
	GOTO :eof
)
echo "usage: kubectl canvaslogs (comp|sman|depapi|apiistio) [componentfilter]"
echo "       needs python with 'pip install rich'"
