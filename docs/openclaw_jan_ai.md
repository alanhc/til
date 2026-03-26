curl -i http://127.0.0.1:1337/v1/models \
  -H "Authorization: Bearer af58535853"


wsl --version
wsl -l -v
type $env:USERPROFILE\.wslconfig
wsl --shutdown


%UserProfile%\.wslconfig
[wsl2]
networkingMode=mirrored
