# wezztershier
(noun) : something clever later  

check .tool-versions for my python version;

the convenience below is predicated on it being `pip install`ed within a valid environment.

dev setup:
  - clone this repo
  - run the following from the local clone
  ```
  python -m venv .wezzenv
  source .wezzenv/bin/activate

  pip install -e
  ```

  - can run with `wezztershier` or `python -m wezztershier` to test interpreter things
    - must be in an environment `pip install -e`'d into

otherwise the usual way with the `python ..` or `python3 ...` or whatever flavor you prefer
