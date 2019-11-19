# Welcome!
This project is spearheaded by the Trash Monks wiki editing team for the Caves of Qud community. We coordinate in the [official Caves of Qud Discord server](https://discordapp.com/invite/cavesofqud) (invite link).

Contributions from the community in the form of issues or pull requests are welcomed. The Trash Monks team is also available to join on the Discord server by asking any of the Mayors there.

This project uses the Code of Conduct available from that Discord server, in the `#code-of-conduct` channel.

# Environment setup
To develop on this project, have Python 3.7 installed on your system, then `git clone` the repo to your hard drive and set up a virtual environment by running `pipenv` in the repo directory:
```bash
python -m pip install --user pipenv  # install pipenv on your system
cd repo-folder                       # insert your repo directory
python -m pipenv install --dev       # create a virtual environment for the current directory
                                     # and install requirements from Pipfile,
                                     # including development dependencies
```

# Pull requests
Pull requests are welcome. Please run `flake8` and `pytest` to ensure that your code will pass the automatic test first.
