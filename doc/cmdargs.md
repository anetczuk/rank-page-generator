## <a name="main_help"></a> python3 -m rankpagegenerator.main --help
```
usage: rankpagegenerator.main [-h] [-la] [--listtools] {generate,info} ...

rank-page-generator

optional arguments:
  -h, --help       show this help message and exit
  -la, --logall    Log all messages
  --listtools      List tools

subcommands:
  use one of tools

  {generate,info}  one of tools
    generate       generate rank static pages
    info           print model info
```



## <a name="generate_help"></a> python3 -m rankpagegenerator.main generate --help
```
usage: rankpagegenerator.main generate [-h] [-d DATA] --outdir OUTDIR

generate rank static pages

optional arguments:
  -h, --help            show this help message and exit
  -d DATA, --data DATA  Path to data file with model
  --outdir OUTDIR       Path to output directory
```



## <a name="info_help"></a> python3 -m rankpagegenerator.main info --help
```
usage: rankpagegenerator.main info [-h] [-d DATA]

print model info

optional arguments:
  -h, --help            show this help message and exit
  -d DATA, --data DATA  Path to data file with model
```
