import numpy as np
from torch import from_numpy

from watchmal.dataset.h5_dataset import H5Dataset
from watchmal.dataset.cnn_mpmt import transformations

barrel_map_array_idxs = [6, 7, 8, 9, 10, 11, 0, 1, 2, 3, 4, 5, 15, 16, 17, 12, 13, 14, 18]
pmts_per_mpmt = 19


class CNNmPMTDataset(H5Dataset):

    def __init__(self, h5file, mpmt_positions_file, transforms=None, collapse_arrays=False):
        super().__init__(h5file, transforms)
        self.mpmt_positions = np.load(mpmt_positions_file)['mpmt_image_positions']
        self.data_size = np.max(self.mpmt_positions, axis=0) + 1
        n_channels = pmts_per_mpmt
        self.data_size = np.insert(self.data_size, 0, n_channels)
        self.collapse_arrays = collapse_arrays

        self.transforms = transforms
        if self.transforms is not None:
            for transform_name in transforms:
                assert hasattr(transformations, transform_name), f"Error: There is no defined transform named {transform_name}"
            transform_funcs = [getattr(transformations, transform_name) for transform_name in transforms]
            self.transforms = transform_funcs
            self.n_transforms = len(self.transforms)

    def get_data(self, hit_pmts, hit_charges, hit_times):
        hit_mpmts = hit_pmts // pmts_per_mpmt
        hit_pmt_in_modules = hit_pmts % pmts_per_mpmt
        hit_rows = self.mpmt_positions[hit_mpmts, 0]
        hit_cols = self.mpmt_positions[hit_mpmts, 1]
        data = np.zeros(self.data_size)
        data[hit_pmt_in_modules, hit_rows, hit_cols] = hit_charges

        # fix barrel array indexing to match endcaps in xyz ordering
        data[:, 12:28, :] = data[barrel_map_array_idxs, 12:28, :]

        # collapse arrays if desired
        if self.collapse_arrays:
            data = np.expand_dims(np.sum(data, 0), 0)
        processed_data = from_numpy(data)

        if self.transforms is not None:
            selection = np.random.choice(2, self.n_transforms)
            for i, transform in enumerate(self.transforms):
                if selection[i]:
                    processed_data = transform(processed_data)

        return processed_data
