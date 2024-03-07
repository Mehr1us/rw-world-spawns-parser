# rw-world-spawns-parser
retrieves all of the spawns each slugcat from world file (tool for wiki)

simplest way to run is to copy a `world_XX.txt` over to same folder as the py script  
then run the following on a cmd opened in same folder: 
```bash
py world-parser.py -file "world_XX.txt"
```

## flags
| flag     							 | arg     | desc                        										    |  
| ---------------------------- | ------- | ----------------------------------------------------------- |  
| `-debug` 						    |         | enables debug logging                                       |  
| `-file`/`-path`/`-world`     | string  | path to load world file from                                |
| `-char`/`-scug`/`slug`       | string  | if included will only get the spawns for the specified scug |
| `+SCUG`                      | n/a     | adds the SCUG to the list of scugs to parse for             |