/mnt/c/Users/leozy/.pyenv/
/home/leoz/.pyenv/

## remove from the first and second place in User Environment Variables:
%PYENV%bin
%PYENV%shims


PS C:\Users\leozy> wsl --set-default-version 2history

"Windows Subsystem for Linux" or "XTerm"
$ sudo apt-get update --yes
$ sudo apt-get install git gcc make openssl libssl-dev libbz2-dev libreadline-dev libsqlite3-dev zlib1g-dev libncursesw5-dev libgdbm-dev libc6-dev zlib1g-dev libsqlite3-dev tk-dev libssl-dev openssl libffi-dev
$ sudo apt install liblzma-dev
$ curl https://pyenv.run | bash
$ vi ~/.bashrc
$ source ~/.bashrc
$ pyenv install 3.10.8
$ pyenv global 3.10.8
$ python -m venv .venv_ubu
$ source .venv_ubu/bin/activate
$ pip freeze > requirements.txt
$ python -m pip download --trusted-host=pypi.org --trusted-host=files.pythonhosted.org --only-binary :all: --dest ./ubu_wheels --no-cache -r requirements.txt