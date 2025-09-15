# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/KPandaK/metaeditor_safetensors/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                     |    Stmts |     Miss |   Cover |   Missing |
|--------------------------------------------------------- | -------: | -------: | ------: | --------: |
| metaeditor\_safetensors/models/metadata\_keys.py         |       10 |        0 |    100% |           |
| metaeditor\_safetensors/models/metadata\_model.py        |       42 |        0 |    100% |           |
| metaeditor\_safetensors/models/settings.py               |       11 |        0 |    100% |           |
| metaeditor\_safetensors/models/theme.py                  |       75 |        0 |    100% |           |
| metaeditor\_safetensors/services/config\_service.py      |       74 |        1 |     99% |        22 |
| metaeditor\_safetensors/services/css\_service.py         |       12 |        0 |    100% |           |
| metaeditor\_safetensors/services/file\_service.py        |       21 |        0 |    100% |           |
| metaeditor\_safetensors/services/image\_service.py       |       32 |        1 |     97% |        58 |
| metaeditor\_safetensors/services/safetensors\_service.py |       69 |        5 |     93% |142, 161-164 |
| metaeditor\_safetensors/services/save\_worker.py         |       18 |        0 |    100% |           |
| metaeditor\_safetensors/services/theme\_service.py       |      191 |       78 |     59% |32-34, 48, 67-68, 76, 83-92, 95-99, 106-121, 143-144, 147, 150-151, 155-158, 167-169, 177-179, 185-186, 190-192, 195-206, 221-226, 246-248, 253, 272-282, 290-291, 297-298 |
| metaeditor\_safetensors/views/about\_dialog.py           |       69 |       69 |      0% |     1-119 |
| metaeditor\_safetensors/views/main\_view.py              |      200 |      200 |      0% |    13-401 |
| metaeditor\_safetensors/views/settings\_dialog.py        |      120 |      120 |      0% |     1-205 |
| metaeditor\_safetensors/views/thumbnail\_dialog.py       |       18 |       18 |      0% |      1-31 |
|                                                **TOTAL** |  **962** |  **492** | **49%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/KPandaK/metaeditor_safetensors/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/KPandaK/metaeditor_safetensors/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/KPandaK/metaeditor_safetensors/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/KPandaK/metaeditor_safetensors/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2FKPandaK%2Fmetaeditor_safetensors%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/KPandaK/metaeditor_safetensors/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.