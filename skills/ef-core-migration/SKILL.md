---
name: ef-core-migration
description: |
  Entity Framework Core migration management for .NET projects. Use when: creating migrations,
  applying updates, rolling back, troubleshooting migration issues, or user says "create migration",
  "update database", "ef migration", "rollback migration", "migration history".
---

# EF Core Migration Management

## Quick Commands

```bash
# Create migration
dotnet ef migrations add {MigrationName} --project {DataProject} --startup-project {ApiProject}

# Apply migrations
dotnet ef database update --project {DataProject} --startup-project {ApiProject}

# Rollback to specific migration
dotnet ef database update {TargetMigration} --project {DataProject} --startup-project {ApiProject}

# Remove last migration (if not applied)
dotnet ef migrations remove --project {DataProject} --startup-project {ApiProject}

# List migrations
dotnet ef migrations list --project {DataProject} --startup-project {ApiProject}

# Generate SQL script
dotnet ef migrations script --project {DataProject} --startup-project {ApiProject} -o migration.sql
```

## Safe Migration Workflow

1. **Backup**: Always backup database before production migrations
2. **Review**: Generate SQL script first, review changes
3. **Test**: Apply to dev/staging before production
4. **Apply**: Use transactions when possible

## Common Patterns

### Adding Column (nullable first)
```csharp
// Step 1: Add nullable column
migrationBuilder.AddColumn<string>(
    name: "NewColumn",
    table: "TableName",
    nullable: true);

// Step 2: Populate data (separate migration)
migrationBuilder.Sql("UPDATE TableName SET NewColumn = 'default' WHERE NewColumn IS NULL");

// Step 3: Make non-nullable (separate migration)
migrationBuilder.AlterColumn<string>(
    name: "NewColumn",
    table: "TableName",
    nullable: false);
```

### Renaming Column
```csharp
migrationBuilder.RenameColumn(
    name: "OldName",
    table: "TableName",
    newName: "NewName");
```

### Adding Index
```csharp
migrationBuilder.CreateIndex(
    name: "IX_TableName_ColumnName",
    table: "TableName",
    column: "ColumnName");
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No migrations found" | Check --project and --startup-project paths |
| "Connection refused" | Ensure database container is running |
| "Pending changes" | Run `dotnet ef migrations add` first |
| "Column already exists" | Check if migration was partially applied |

## Docker Context

```bash
# Run migrations in Docker container
docker exec -it {container} dotnet ef database update --project {DataProject} --startup-project {ApiProject}

# Or from host with connection string
dotnet ef database update --connection "Host=localhost;Port=5432;Database=mydb;Username=user;Password=pass"
```
