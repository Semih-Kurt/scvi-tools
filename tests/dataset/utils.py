from typing import List, Optional

import torch
from anndata import AnnData

from scvi import REGISTRY_KEYS
from scvi.data.anndata import AnnDataManager
from scvi.data.anndata.fields import (
    CategoricalJointObsField,
    CategoricalObsField,
    LayerField,
    NumericalJointObsField,
    ProteinObsmField,
)
from scvi.model import SCVI

use_gpu = torch.cuda.is_available()


def unsupervised_training_one_epoch(
    adata: AnnData,
    run_setup_anndata: bool = True,
    batch_key: Optional[str] = None,
    labels_key: Optional[str] = None,
):
    if run_setup_anndata:
        SCVI.setup_anndata(adata, batch_key=batch_key, labels_key=labels_key)
    m = SCVI(adata)
    m.train(1, train_size=0.4, use_gpu=use_gpu)


def generic_setup_adata_manager(
    adata: AnnData,
    batch_key: Optional[str] = None,
    labels_key: Optional[str] = None,
    categorical_covariate_keys: Optional[List[str]] = None,
    continuous_covariate_keys: Optional[List[str]] = None,
    layer: Optional[str] = None,
    protein_expression_obsm_key: Optional[str] = None,
    protein_names_uns_key: Optional[str] = None,
) -> AnnDataManager:
    batch_field = CategoricalObsField(REGISTRY_KEYS.BATCH_KEY, batch_key)
    anndata_fields = [
        batch_field,
        LayerField(REGISTRY_KEYS.X_KEY, layer, is_count_data=True),
        CategoricalObsField(REGISTRY_KEYS.LABELS_KEY, labels_key),
        CategoricalJointObsField(
            REGISTRY_KEYS.CAT_COVS_KEY, categorical_covariate_keys
        ),
        NumericalJointObsField(REGISTRY_KEYS.CONT_COVS_KEY, continuous_covariate_keys),
    ]
    if protein_expression_obsm_key is not None:
        anndata_fields.append(
            ProteinObsmField(
                REGISTRY_KEYS.PROTEIN_EXP_KEY,
                protein_expression_obsm_key,
                use_batch_mask=True,
                batch_key=batch_field.attr_key,
                colnames_uns_key=protein_names_uns_key,
                is_count_data=True,
            )
        )
    adata_manager = AnnDataManager(fields=anndata_fields)
    adata_manager.register_fields(adata)
    return adata_manager
