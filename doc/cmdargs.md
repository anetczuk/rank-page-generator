## <a name="main_help"></a> python3 -m rankpagegenerator.main --help
```
usage: python3 -m rankpagegenerator.main [-h] [-la] [--listtools]
                                         {generate,info,preparephotos} ...

generate static pages containing rank search based on defined model

options:
  -h, --help            show this help message and exit
  -la, --logall         Log all messages (default: False)
  --listtools           List tools (default: False)

subcommands:
  use one of tools

  {generate,info,preparephotos}
                        one of tools
    generate            generate rank static pages
    info                print model info
    preparephotos       parse license file and prepare photos
```



## <a name="generate_help"></a> python3 -m rankpagegenerator.main generate --help
```
usage: python3 -m rankpagegenerator.main generate [-h] [-d DATA]
                                                  [-t TRANSLATION]
                                                  [--embedscripts EMBEDSCRIPTS]
                                                  [--nophotos NOPHOTOS]
                                                  --outdir OUTDIR

generate rank static pages

options:
  -h, --help            show this help message and exit
  -d DATA, --data DATA  Path to data file with model (default: None)
  -t TRANSLATION, --translation TRANSLATION
                        Path to translation file (default: None)
  --embedscripts EMBEDSCRIPTS
                        Embed scripts into one file (default: False)
  --nophotos NOPHOTOS   Do not generate image galleries (default: False)
  --outdir OUTDIR       Path to output directory (default: None)
```



## <a name="info_help"></a> python3 -m rankpagegenerator.main info --help
```
usage: python3 -m rankpagegenerator.main info [-h] [-d DATA]

print model info

options:
  -h, --help            show this help message and exit
  -d DATA, --data DATA  Path to data file with model (default: None)
```



## <a name="preparephotos_help"></a> python3 -m rankpagegenerator.main preparephotos --help
```
usage: python3 -m rankpagegenerator.main preparephotos [-h] -lf LICENSEFILE
                                                       --outdir OUTDIR

parse license file and prepare photos

options:
  -h, --help            show this help message and exit
  -lf LICENSEFILE, --licensefile LICENSEFILE
                        Path to license file (default: None)
  --outdir OUTDIR       Path to output directory (default: None)
```
