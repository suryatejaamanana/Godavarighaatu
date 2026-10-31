# Proposed Folder Structure

```
godavarighaatu/
  frontend/   app/(shop) app/admin components/{ui,shop,admin} hooks lib services types public/brand
  backend/    app/{api/v1,core,models,schemas,repositories,services,integrations/{payments,shipping},main.py}
              alembic/  tests/  seed/ (development only)
  docs/
  .env.example  .gitignore  README.md
```
