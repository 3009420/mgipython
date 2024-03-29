# All models for the mrk_* tables
from mgipython.modelconfig import db
from ..core import *
from acc import Accession
from mgi import Organism, ReferenceAssoc
from seq import SeqMarkerCache
from voc import VocAnnot

    
class MarkerDetailClipNoteChunk(db.Model,MGIModel):
    __tablename__ = "mrk_notes"
    _marker_key = db.Column(db.Integer,db.ForeignKey("mrk_marker._marker_key"),primary_key=True)
    note = db.Column(db.String())
    sequencenum = db.Column(db.Integer, primary_key=True)

class MarkerLocationCache(db.Model,MGIModel):
    __tablename__="mrk_location_cache"
    _cache_key = db.Column(db.Integer,primary_key=True)
    _marker_key = db.Column(db.Integer,db.ForeignKey("mrk_marker._marker_key"))
    _organism_key = db.Column(db.Integer())
    chromosome = db.Column(db.String())
    cytogeneticoffset = db.Column(db.String())
    cmoffset = db.Column(db.Float())
    genomicchromosome = db.Column(db.String())
    startcoordinate = db.Column(db.Float())
    endcoordinate = db.Column(db.Float())
    strand = db.Column(db.String())
    mapunits = db.Column(db.String())
    provider = db.Column(db.String())
    version = db.Column(db.String())

    @property
    def providerString(self):
        if not self.provider:
            return ""
        return "From %s annotation of %s" % (self.provider, self.version)

    def __repr__(self):
        if not self.startcoordinate or not self.endcoordinate:
            return "Chr%s" % (self.chromosome)
        
        return "Chr%s:%d-%d bp, %s strand" % (self.chromosome,
            self.startcoordinate, self.endcoordinate,
            self.strand)
    
class MarkerStatus(db.Model,MGIModel):
    __tablename__="mrk_status"
    _marker_status_key = db.Column(db.Integer,primary_key=True)
    status = db.Column(db.String())
    
class MarkerType(db.Model,MGIModel):
    __tablename__="mrk_types"
    _marker_type_key = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String())
    
class MarkerMCVCache(db.Model,MGIModel):
    """
    Marker Feature Type Cache table (has generated types like QTL)
    """
    __tablename__="mrk_mcv_cache"
    _marker_key = db.Column(db.Integer,
                            mgi_fk("mrk_marker._marker_key"),
                            primary_key=True)
    _mcvterm_key = db.Column(db.Integer,
                            mgi_fk("voc_term._term_key"),
                            primary_key=True)
    qualifier = db.Column(db.String())
    
class MarkerReferenceCache(db.Model, MGIModel):
    __tablename__ = "mrk_reference"
    _marker_key = db.Column(db.Integer, 
                            mgi_fk("mrk_marker._marker_key"),
                            primary_key=True)
    _refs_key = db.Column(db.Integer, 
                            mgi_fk("bib_refs._refs_key"),
                            primary_key=True)
    
    
class Marker(db.Model,MGIModel):
    __tablename__="mrk_marker"
    _marker_key=db.Column(db.Integer,primary_key=True)
    _organism_key=db.Column(db.Integer())
    _organism_key.hidden=True
    _marker_type_key=db.Column(db.Integer())
    _marker_type_key.hidden=True
    _marker_status_key=db.Column(db.Integer())
    _marker_status_key.hidden=True
    symbol=db.Column(db.String())
    name=db.Column(db.String())
    chromosome=db.Column(db.String())
    cytogeneticoffset=db.Column(db.String())

    #constants
    _mgitype_key=2
    _mcv_annottype_key=1011
    # the biotype conflict term
    _biotypeconflict_yes_key = 5420767
    
    # joined fields
    organism = db.column_property(
                db.select([Organism.commonname]).
                where(Organism._organism_key==_organism_key)
        )  
    markertype = db.column_property(
                db.select([MarkerType.name]).
                where(MarkerType._marker_type_key==_marker_type_key)
        )  

    markerstatus = db.column_property(
                db.select([MarkerStatus.status]).
                where(MarkerStatus._marker_status_key==_marker_status_key).
                label("markerstatus")
        )

    #mgiid = db.Column(db.String())
    mgiid = db.column_property(
        db.select([Accession.accid]).
        where(db.and_(Accession._mgitype_key==_mgitype_key,
            Accession.prefixpart=='MGI:', 
            Accession.preferred==1, 
            Accession._logicaldb_key==1, 
            Accession._object_key==_marker_key)) 
    )
    
    # joined relationship
    
    # alleles
    # alleles backref defined in Allele class
    
    mgiid_object = db.relationship("Accession",
                    primaryjoin="and_(Accession._object_key==Marker._marker_key,"
                                    "Accession.prefixpart=='MGI:',"
                                    "Accession.preferred==1,"
                                    "Accession._logicaldb_key==1,"
                                    "Accession._mgitype_key==%d)" % _mgitype_key,
                    foreign_keys="[Accession._object_key]",
                    uselist=False)
    
    featuretype_vocterms = db.relationship("VocTerm",
                    primaryjoin="and_(MarkerMCVCache._marker_key==Marker._marker_key,"
                                "MarkerMCVCache.qualifier=='D')",
                    secondary=MarkerMCVCache.__table__,
                    foreign_keys="[MarkerMCVCache._marker_key, MarkerMCVCache._mcvterm_key]")

    secondary_mgiids = db.relationship("Accession",
            primaryjoin="and_(Accession._object_key==Marker._marker_key,"
                "Accession.preferred==0,"
                "Accession.prefixpart=='MGI:',"
                "Accession._logicaldb_key==1,"
                "Accession._mgitype_key==%s)" % _mgitype_key,
            foreign_keys="[Accession._object_key]",
            order_by="Accession.accid")
    
    
    biotype_sequences = db.relationship("SeqMarkerCache",
            primaryjoin="and_(SeqMarkerCache._marker_key==Marker._marker_key,"
                "SeqMarkerCache.rawbiotype!=None)",
            foreign_keys="[SeqMarkerCache._marker_key]",
            order_by="SeqMarkerCache._logicaldb_key,SeqMarkerCache.accid")
    

    locations = db.relationship("MarkerLocationCache",
        primaryjoin="Marker._marker_key==MarkerLocationCache._marker_key",
        foreign_keys="[MarkerLocationCache._marker_key]")
    
    synonyms = db.relationship("Synonym",
        primaryjoin="and_(Marker._marker_key==Synonym._object_key, " 
                "Synonym._mgitype_key==%d)" % _mgitype_key,
        order_by="Synonym.synonym",
        foreign_keys="[Synonym._object_key]")

    detailclipchunks = db.relationship("MarkerDetailClipNoteChunk",
        primaryjoin= "MarkerDetailClipNoteChunk._marker_key==Marker._marker_key",
        order_by="MarkerDetailClipNoteChunk.sequencenum",
        foreign_keys="[MarkerDetailClipNoteChunk._marker_key]")
    
    # only direct references via mgi_reference_assoc
    explicit_references = db.relationship("Reference",
        secondary=ReferenceAssoc.__table__,
        primaryjoin="and_(Marker._marker_key==ReferenceAssoc._object_key, "
                            "ReferenceAssoc._mgitype_key==%d)" % _mgitype_key,
        secondaryjoin="ReferenceAssoc._refs_key==Reference._refs_key",
        foreign_keys="[Marker._marker_key,Reference._refs_key]",
        backref="explicit_markers"
     )
    
    # all marker references
    all_references = db.relationship("Reference",
        secondary=MarkerReferenceCache.__table__,
        backref="all_markers")
    
    
    expression_assays = db.relationship("Assay",
        primaryjoin="Marker._marker_key==Assay._marker_key",
        foreign_keys="[Assay._marker_key]",
        backref=db.backref("marker", uselist=False))
    
    # antibodies
    # backref defined in Antibody class
    
    # antibodypreps
    # backref in AntibodyPrep class
    
    # mapping_experiment_assocs
    # backref in ExperimentMarkerAssoc class
    
    # sequences
    # backref in Sequence class
    
    @classmethod
    def has_explicit_references(self):
        q = self.query.filter(Marker.explicit_references.any())
        return db.object_session(self).query(db.literal(True)) \
            .filter(q.exists()).scalar()
            
    @property
    def has_biotypeconflict(self):
        """
        Requires loading self.biotype_sequences
        """
        conflict = False
        if self.biotype_sequences:
            
            for seq_cache in self.biotype_sequences:
                
                if seq_cache._biotypeconflict_key == self._biotypeconflict_yes_key:
                    conflict = True
            
        return conflict

    @property
    def featuretype(self):
        featuretype = ''
        if self.featuretype_vocterms:
            featuretype = ", ".join([t.term for t in self.featuretype_vocterms])
        return featuretype
        
    @property
    def secondaryids(self):
        ids = [a.accid for a in self.secondary_mgiids]
        return ids

    @property
    def replocation(self):
        return self.locations and self.locations[0] or None

    @property
    def detailclipnote(self):
        return "".join([nc.note for nc in self.detailclipchunks])

    def __repr__(self):
        return "<Marker %s>"%self.symbol
