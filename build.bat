@echo off

set VENV=%~dp0.venv

IF NOT EXIST "%VENV%" (
    echo.
    echo creating python venv for setuptools
    echo.
    python -m venv %VENV% || exit /b 1
)

set PYTHON=%VENV%\Scripts\python
echo.
echo installing setuptools to venv
echo.
%PYTHON% -m pip install -q -r requirements.txt || exit /b 1
echo.
echo building package
echo.
%PYTHON% -m build || exit /b 1
