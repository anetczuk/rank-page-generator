## <a name="main_help"></a> python3 -m rankpagegenerator.main --help
```
usage: python3 -m rankpagegenerator.main [-h] [-la] [--listtools]
                                         {generate,info} ...

generate static pages containing rank search based on defined model

optional arguments:
  -h, --help       show this help message and exit
  -la, --logall    Log all messages (default: False)
  --listtools      List tools (default: False)

subcommands:
  use one of tools

  {generate,info}  one of tools
    generate       generate rank static pages
    info           print model info
```



## <a name="generate_help"></a> python3 -m rankpagegenerator.main generate --help
```
usage: python3 -m rankpagegenerator.main generate [-h] [-d DATA]
                                                  [--embedscripts EMBEDSCRIPTS]
                                                  --outdir OUTDIR

generate rank static pages

optional arguments:
  -h, --help            show this help message and exit
  -d DATA, --data DATA  Path to data file with model (default: None)
  --embedscripts EMBEDSCRIPTS
                        Embed scripts into one file (default: False)
  --outdir OUTDIR       Path to output directory (default: None)
```



## <a name="info_help"></a> python3 -m rankpagegenerator.main info --help
```
usage: python3 -m rankpagegenerator.main info [-h] [-d DATA]

print model info

optional arguments:
  -h, --help            show this help message and exit
  -d DATA, --data DATA  Path to data file with model (default: None)
```
