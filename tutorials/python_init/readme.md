# pyenv
https://realpython.com/intro-to-pyenv/
https://github.com/pyenv-win/pyenv-win

# venv
https://mothergeo-py.readthedocs.io/en/latest/development/how-to/venv-win.html


# pyenv - anaconda
Advanced system settings/Environment Variables
Move pyenv above anaconda in the path
PYENV: C:\Users\leozy\.pyenv\pyenv-win\
%PYENV%bin;%PYENV%shims


$ pyenv --list

$pyenv --version
$ pyenv versions
$ pyenv install --list | grep -E "3\.(8|10)\..+"
$ pyenv install 3.7.9
$ pyenv global 3.7.9


$ python -m venv .venv
$ source .venv/Scripts/activate
>.venv\Scripts\activate
$ pip install -r requirements.txt [--no-index -f ./wheels/]
$ pip freeze > requirements_all.txt
$ python -m pip download --trusted-host=pypi.org --trusted-host=files.pythonhosted.org --only-binary :all: --dest ./wheels_all --no-cache -r requirements_all.txt
$ pip install -r requirements_all.txt --no-index -f ./wheels_all/ --upgrade