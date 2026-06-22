# Diario Oficial - Buscador HTML

Interface estatica para consultar publicacoes do Diario Municipal AMM-MG.

## Publicar no GitHub Pages

1. Envie o arquivo `index.html` para um repositorio no GitHub.
2. Abra `Settings > Pages`.
3. Em `Build and deployment`, selecione `Deploy from a branch`.
4. Escolha a branch e a pasta onde esta o `index.html`.
5. Acesse a URL gerada pelo GitHub Pages.

## Observacao

Por ser uma pagina estatica, ela precisa de um proxy de leitura para buscar o site do Diario Municipal pelo navegador. O campo `Proxy` vem como `auto`, tentando alguns caminhos publicos. Se a busca falhar por proxy, informe no campo um proxy proprio no formato:

```text
https://seu-proxy.exemplo/?url=
```
