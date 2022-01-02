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

# Using a local Hagadias in a pipenv
By default, projects that include hagadias in their pipfile will use the hagadias hosted on git, but these are the steps to take to make the pipenv read your local hagadias folder instead. Testing out local changes on Hagadias to for other connected Trash Monk projects is recommended to make sure the outcomes for those projects are correct. This assumes that the pipfile already has hagadias.

Look up how to change your system environment variables. For Windows, this can be done by searching "System environment" and select "Edit System environment variables" and then select the "Environment Variables..." in the Advanced Tab. 

Create a new system variable (or user variable if installed locally) called `PYTHONPATH` and set the value to your hagadias directory (Ex. `C:\Users\(you)\Documents\github\hagadias\`). This must end in a backslash to read the whole folder instead of just the folder file itself!

Start a new terminal and run your program of choice in the pipenv shell.

This makes python read the hagadias folder every time you run something. This may cause issues if you are working on unrelated projects that use py files that share the same name as some in hagadias. If this is of concern, be sure to remove the PYTHONPATH variable once you're done with hagadias development.

# Running tests
In order to run the test suite, create a file in your `hagadias` project development directory called
`game_location_for_tests`. The only contents of this file should be a path to the installation directory of
Caves of Qud, with no other characters.

Activate the venv with:
```
pipenv shell
```
and then run:
```
python -m pytest
```


# Pull requests
Pull requests are welcome. Please run `flake8` and `pytest` to ensure that your code will pass the automatic test first.
