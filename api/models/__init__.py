"""Model registry_loader lives here so api/models/ is a plain package;
avoids a name collision with api/registry/ (the SQLite model-governance
registry, a different concept from "which model classes exist")."""
