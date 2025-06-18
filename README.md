# Teacher UC - Backend

Revisar documentación en el [informe correspondiente a la Entrega 3](https://uccl0-my.sharepoint.com/:w:/r/personal/vicentemoreno_uc_cl/Documents/LoremIpsum/Informe%20Entrega%203.docx?d=w5b22cf5c0bfb4f699f44017dc8028082&csf=1&web=1&e=Ww5NqF).

## Tests

Los tests están escritos con la librería `unittest` de Python. Estos pueden ejecutarse con

```
python -m unittest discover --start-directory tests
```

Por otro lado, el coverage puede obtenerse con

```
python -m coverage run -m unittest discover --start-directory tests && python -m coverage report --omit="*/tests/*"
```
