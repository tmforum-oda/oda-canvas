# Dependent API Discovery Tool

This program takes an oas_specification and a local ComponentRegistry endpoint as input and then starts searching vor ExposedAPIs, which implement the given oas_specification in the local ComponentRegistry.
If there are no matches in the local ComponentRegistry it propagates the search to the upstream repositories and returns all matches from there. If again there are no matches the next level of upstream ComponentRegistries is queried and so on. if on the top level upstream ComponentRegisitry there are no matches an empty result is returned.
