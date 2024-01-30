```mermaid
    classDiagram
        RootSourceCollections o--> ASourceCollection

        ASourceCollection o-->"recursively" ASourceCollection

        ASourceCollection <|-- NullSourceCollection

        ASourceCollection <|-- SourceCollection

        ASourceCollection <|-- SubSourceCollection

        ASourceCollection "1"o-->"1..*" SourceObject

        ASourceCollection ..>"use" SetupObject

        SetupObject "0..*"o-->"1..*" ISetupCommand

        SourceObject ..>"create" SetupObject

        ASourceCollection ..>"use" AReleaseCollection

        ReleaseCollections "1"o-->"1..*" AReleaseCollection

        AReleaseCollection <|-- ReleaseCollection
        ReleaseCollection "1"o-->"1..*" ReleaseObject

        AReleaseCollection <|-- SubReleaseCollection
        SubReleaseCollection "1"o-->"1..*" SubReleaseObject

        ASourceCollection ..>"create" AReleaseObject

        AReleaseObject <|-- ReleaseObject
        AReleaseObject <|-- SubReleaseObject

        Translator o--> ReleaseCollections
        Translator o--> MaterialTranslator
        Translator o--> ANameTranslator
        Translator o--> ContainerCollection
        Translator ..>"use" AReleaseCollection
        Translator ..>"create" AFinalObject

        ANameTranslator <|-- BoneGroupTranslator
        ANameTranslator <|-- ShapeKeyTranslator

        ANameTranslator o--> ProfileHandler

        ProfileHandler <|-- ProfileReader
        ProfileHandler <|-- ProfileWriter

        ContainerCollection "1"o-->"1..*" ContainerObject

        AFinalObject <|-- TranslatedObject
        AFinalObject <|-- DefaultObject

        TranslatedCollection "1"o-->"1..*" TranslatedObject
        DefaultCollection "1"o-->"1..*" DefaultObject
        
        Feedback o--> ContainerCollection
        Feedback o--> AFinalCollection

        AFinalCollection <|-- TranslatedCollection
        AFinalCollection <|-- DefaultCollection

        MaterialCombiner "1"o-->"1..2" AFinalCollection
        MaterialCombiner ..>"use" ExternalAddonTool
        MaterialCombiner "1"..>"1..* create" TextureImage

        CollectionUtils "use"<.. ASourceCollection
        CollectionUtils "use"<.. AReleaseCollection
        CollectionUtils "use"<.. ContainerCollection
        CollectionUtils "use"<.. AFinalCollection

        class RootSourceCollections
            RootSourceCollections: list_of_ASourceCollection  member
            RootSourceCollections: update() RootSourceCollections
            RootSourceCollections: queue() RootSourceCollections
            RootSourceCollections: setup() list_of_AReleaseObject

        class ASourceCollection
            <<Abstract>> ASourceCollection
            ASourceCollection: ASourceCollection parent
            ASourceCollection: "bpy.types.Collection" -real
            ASourceCollection: list_of_SourceObject objects
            ASourceCollection: setup() AReleaseObject
            ASourceCollection: update() ASourceCollection

        class SourceObject
            <<ValueObject>> SourceObject
            SourceObject: "bpy.types.Object" -real
            SourceObject: create_setup_object() SetupObject

        class SetupObject
            <<ValueObject>> SetupObject
            SetupObject: "bpy.types.Object" -real
            SetupObject: setup()

        class ISetupCommand
            <<Interface>> ISetupCommand

        class AReleaseObject
            <<Abstract>> AReleaseObject
            AReleaseObject: "bpy.types.Object" -real
            AReleaseObject: delete()
            AReleaseObject: register_to_collection()

        class AReleaseCollection
            <<Abstract>> AReleaseCollection
            AReleaseCollection: "bpy.types.Collection" -real
            AReleaseCollection: list_of_AReleaseObject objects
            AReleaseCollection: update() AReleaseCollection
            AReleaseCollection: find_object() AReleaseObject

        class ReleaseCollections
            ReleaseCollections
            ReleaseCollections: update() ReleaseCollections

        class ReleaseObject
            <<ValueObject>> ReleaseObject

        class SubReleaseObject
            <<ValueObject>> SubReleaseObject

        class TranslatedObject
            <<ValueObject>> TranslatedObject

        class DefaultObject
            <<ValueObject>> DefaultObject

        class ContainerObject
            <<ValueObject>> ContainerObject
            ContainerObject: "bpy.types.Object" -real
            ContainerObject: delete()
            ContainerObject: register_to_collection()

        class TextureImage
            <<ValueObject>> TextureImage
            TextureImage: "bpy.types.Image" -real

        class AFinalCollection
            <<Abstract>> AFinalCollection
            AFinalCollection: "bpy.types.Collection" -real
            AFinalCollection: list_of_AFinalObject objects
            AFinalCollection: update() AFinalCollection
            AFinalCollection: find_object() AFinalObject

        class Translator
            Translator: translate()

        class MaterialCombiner
            MaterialCombiner: combine_materials()

        class Feedback
            Feedback: feedback_to_container()

        class ContainerCollection
            ContainerCollection: "bpy.types.Collection" -real
            ContainerCollection: list_of_ContainerObject objects
            ContainerCollection: update() ContainerCollection
            ContainerCollection: find_object() ContainerObject

        class AFinalObject
            <<Abstract>> AFinalObject
            AFinalObject: "bpy.types.Object" -real
            AFinalObject: delete()
            AFinalObject: register_to_collection()


        class CollectionUtils
            CollectionUtils: update()$
            CollectionUtils: find_object()$
```