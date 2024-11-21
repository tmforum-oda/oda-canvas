@echo off

SET CANVASLOGS_FOLDER=%~dp0

SET PYTHON=python
IF EXIST c:\dev\venv\canvaslogs\Scripts\python.exe (
	SET PYTHON=c:\dev\venv\canvaslogs\Scripts\python.exe
)

SET FOLLOW=
if "%1" == "-f" (
	SET FOLLOW=-f
	shift
)

SET OPERATOR=%1
shift

SET COMP_PATTERN=
SET TEMP=%1-
if not "%TEMP:~0,1%" == "-" (
	SET COMP_PATTERN=-c %1
    shift
)


if "%OPERATOR%" == "comp" (
	kubectl logs -n canvas deployment/component-operator -c component-operator %FOLLOW% | %PYTHON% %CANVASLOGS_FOLDER%\showlogtree.py %COMP_PATTERN% %FOLLOW% %1 %2 %3 %4 %5 %6 %7 %8 %9
	GOTO :eof
)
if "%OPERATOR%" == "sman" (
	kubectl logs -n canvas deployment/canvas-smanop %FOLLOW% | %PYTHON% %CANVASLOGS_FOLDER%\showlogtree.py %COMP_PATTERN% %FOLLOW% %1 %2 %3 %4 %5 %6 %7 %8 %9
	GOTO :eof
)
if "%OPERATOR%" == "depapi" (
	kubectl logs -n canvas deployment/canvas-depapi-op %FOLLOW% | %PYTHON% %CANVASLOGS_FOLDER%\showlogtree.py %COMP_PATTERN% %FOLLOW% %1 %2 %3 %4 %5 %6 %7 %8 %9
	GOTO :eof
)
if "%OPERATOR%" == "apiistio" (
	kubectl logs -n canvas deployment/api-operator-istio %FOLLOW% | %PYTHON% %CANVASLOGS_FOLDER%\showlogtree.py %COMP_PATTERN% %FOLLOW% %1 %2 %3 %4 %5 %6 %7 %8 %9
	GOTO :eof
)

echo "                                                                                                "
echo "usage: kubectl canvaslogs [-f] (comp|sman|depapi|apiistio) [<componentfilter>] [-l <last-hours>]"
echo "       needs python with 'pip install rich timedinput'                                          "
echo "                                                                                                "
echo "options:                                                                                        "
echo "  -f, (follow)        keep the Log Viewer open and update the display on incoming logs          "
echo "  <component-filter>  filter components by name with wildcards (*/?), e.g. comp-a-*             "
echo "  -l <last-hours>     only look at the last n hours in logfile                                  "
echo "                                                                                                "
