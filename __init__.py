
bl_info = {
    "name": "Arcsys MUA Importer & Exporter",
    "author": "Tianling",
    "version": (0, 0, 1),
    "blender": (2, 8, 0),
    "location": "File > Import-Export",
    "description": "Import and export MUA files",
    "warning": "",
    "category": "Import-Export",
    }

if "bpy" in locals():
    import importlib
    if "importer" in locals():
        importlib.reload(importer)
    if "exporter" in locals():
        importlib.reload(exporter)

def register():
    from .exporter import register_exporter
    register_exporter()
    from .importer import register_importer
    register_importer()


def unregister():
    from .exporter import unregister_exporter
    unregister_exporter()
    from .importer import unregister_importer
    unregister_importer()
