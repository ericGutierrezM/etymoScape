# EtymoScape Web

Production UI backbone for EtymoScape.

The app reads the existing JSON files from:

```text
../../data/final_data
```

Routes are dynamic. For example:

```text
/word/sugar
```

is rendered by:

```text
src/app/word/[slug]/page.tsx
```

and loads:

```text
../../data/final_data/sugar_final.json
```

## Run

```bash
npm install
npm run dev
```

Then open:

```text
http://localhost:3000
```
