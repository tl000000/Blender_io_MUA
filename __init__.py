

bl_info = {
    "name": "Arcsys MUA Importer & Exporter",
    "author": "Tianling",
    "version": (0, 0, 1),
    "blender": (3, 5, 1),
    "location": "File > Import-Export",
    "description": "Import and export MUA files",
    "warning": "",
    "category": "Import-Export",
    }


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
