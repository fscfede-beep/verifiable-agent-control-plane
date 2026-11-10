@echo off
powershell -ExecutionPolicy Bypass -File "%~dp0twin\prepare-environment.ps1" %*
