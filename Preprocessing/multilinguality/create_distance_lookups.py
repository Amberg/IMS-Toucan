import argparse
import json
import os.path

import torch
from geopy.distance import geodesic
from huggingface_hub import hf_hub_download
from tqdm import tqdm

from Preprocessing.multilinguality.MetricMetaLearner import create_learned_cache
from Utility.utils import load_json_from_path


class CacheCreator:
    def __init__(self, cache_root="."):
        self.iso_codes = list(load_json_from_path(hf_hub_download(repo_id="Flux9665/ToucanTTS", filename="iso_to_fullname.json")).keys())
        self.iso_lookup = load_json_from_path(hf_hub_download(repo_id="Flux9665/ToucanTTS", filename="iso_lookup.json"))
        self.cache_root = cache_root
        self.pairs = list()  # ignore order, collect all language pairs
        for index_1 in tqdm(range(len(self.iso_codes)), desc="Collecting language pairs"):
            for index_2 in range(index_1, len(self.iso_codes)):
                self.pairs.append((self.iso_codes[index_1], self.iso_codes[index_2]))

    def create_tree_cache(self, cache_root="."):
        iso_to_family_memberships = load_json_from_path(hf_hub_download(repo_id="Flux9665/ToucanTTS", filename="iso_to_fullname.json"))

        self.pair_to_tree_distance = dict()
        for pair in tqdm(self.pairs, desc="Generating tree pairs"):
            lang_1 = pair[0]
            lang_2 = pair[1]
            depth_of_l1 = len(iso_to_family_memberships[lang_1])
            depth_of_l2 = len(iso_to_family_memberships[lang_2])
            depth_of_lca = len(set(iso_to_family_memberships[pair[0]]).intersection(set(iso_to_family_memberships[pair[1]])))
            self.pair_to_tree_distance[pair] = (depth_of_l1 + depth_of_l2) - (2 * (depth_of_lca + 1) if depth_of_lca > 1 else depth_of_lca)  # with discounting for added importance of earlier nodes
        min_dist = min(self.pair_to_tree_distance.values())
        max_dist = max(self.pair_to_tree_distance.values())
        for pair in self.pair_to_tree_distance:
            if pair[0] == pair[1]:
                self.pair_to_tree_distance[pair] = 0.0
            else:
                self.pair_to_tree_distance[pair] = (self.pair_to_tree_distance[pair] + abs(min_dist)) / (max_dist + abs(min_dist))
        lang_1_to_lang_2_to_tree_dist = dict()
        for pair in tqdm(self.pair_to_tree_distance):
            lang_1 = pair[0]
            lang_2 = pair[1]
            dist = self.pair_to_tree_distance[pair]
            if lang_1 not in lang_1_to_lang_2_to_tree_dist.keys():
                lang_1_to_lang_2_to_tree_dist[lang_1] = dict()
            lang_1_to_lang_2_to_tree_dist[lang_1][lang_2] = dist
        with open(os.path.join(cache_root, 'lang_1_to_lang_2_to_tree_dist.json'), 'w', encoding='utf-8') as f:
            json.dump(lang_1_to_lang_2_to_tree_dist, f, ensure_ascii=False, indent=4)

    def create_map_cache(self, cache_root="."):
        self.pair_to_map_dist = dict()
        iso_to_long_lat = load_json_from_path(hf_hub_download(repo_id="Flux9665/ToucanTTS", filename="iso_to_long_lat.json"))
        for pair in tqdm(self.pairs, desc="Generating map pairs"):
            try:
                long_1, lat_1 = iso_to_long_lat[pair[0]]
                long_2, lat_2 = iso_to_long_lat[pair[1]]
                geodesic((lat_1, long_1), (lat_2, long_2))
                self.pair_to_map_dist[pair] = geodesic((lat_1, long_1), (lat_2, long_2)).miles
            except KeyError:
                pass
        lang_1_to_lang_2_to_map_dist = dict()
        for pair in self.pair_to_map_dist:
            lang_1 = pair[0]
            lang_2 = pair[1]
            dist = self.pair_to_map_dist[pair]
            if lang_1 not in lang_1_to_lang_2_to_map_dist.keys():
                lang_1_to_lang_2_to_map_dist[lang_1] = dict()
            lang_1_to_lang_2_to_map_dist[lang_1][lang_2] = dist

        with open(os.path.join(cache_root, 'lang_1_to_lang_2_to_map_dist.json'), 'w', encoding='utf-8') as f:
            json.dump(lang_1_to_lang_2_to_map_dist, f, ensure_ascii=False, indent=4)

    def create_oracle_cache(self, model_path, cache_root="."):
        """Oracle language-embedding distance of supervised languages is only used for evaluation, not usable for zero-shot.

        Note: The generated oracle cache is only valid for the given `model_path`!"""
        loss_fn = torch.nn.MSELoss(reduction="mean")
        self.pair_to_oracle_dist = dict()
        lang_embs = torch.load(model_path)["model"]["encoder.language_embedding.weight"]
        lang_embs.requires_grad_(False)
        for pair in tqdm(self.pairs, desc="Generating oracle pairs"):
            try:
                dist = loss_fn(lang_embs[self.iso_lookup[-1][pair[0]]], lang_embs[self.iso_lookup[-1][pair[1]]]).item()
                self.pair_to_oracle_dist[pair] = dist
            except KeyError:
                pass
        lang_1_to_lang_2_oracle_dist = dict()
        for pair in self.pair_to_oracle_dist:
            lang_1 = pair[0]
            lang_2 = pair[1]
            dist = self.pair_to_oracle_dist[pair]
            if lang_1 not in lang_1_to_lang_2_oracle_dist.keys():
                lang_1_to_lang_2_oracle_dist[lang_1] = dict()
            lang_1_to_lang_2_oracle_dist[lang_1][lang_2] = dist
        with open(os.path.join(cache_root, "lang_1_to_lang_2_to_oracle_dist.json"), "w", encoding="utf-8") as f:
            json.dump(lang_1_to_lang_2_oracle_dist, f, ensure_ascii=False, indent=4)

    def create_learned_cache(self, model_path, cache_root="."):
        """Note: The generated learned distance cache is only valid for the given `model_path`!"""
        create_learned_cache(model_path, cache_root=cache_root)

    def create_required_files(self, model_path, create_oracle=False):
        if not os.path.exists(os.path.join(self.cache_root, "lang_1_to_lang_2_to_tree_dist.json")) or os.path.exists(hf_hub_download(repo_id="Flux9665/ToucanTTS", filename="lang_1_to_lang_2_to_tree_dist.json")):
            self.create_tree_cache(cache_root="Preprocessing/multilinguality")
        if not os.path.exists(os.path.join(self.cache_root, "lang_1_to_lang_2_to_map_dist.json")) or os.path.exists(hf_hub_download(repo_id="Flux9665/ToucanTTS", filename="lang_1_to_lang_2_to_map_dist.json")):
            self.create_map_cache(cache_root="Preprocessing/multilinguality")
        if not os.path.exists(os.path.join(self.cache_root, "asp_dict.pkl")) or os.path.exists(hf_hub_download(repo_id="Flux9665/ToucanTTS", filename="asp_dict.pkl")):
            raise FileNotFoundError("asp_dict.pkl must be downloaded separately.")
        if not os.path.exists(os.path.join(self.cache_root, "lang_1_to_lang_2_to_learned_dist.json")) or os.path.exists(hf_hub_download(repo_id="Flux9665/ToucanTTS", filename="lang_1_to_lang_2_to_learned_dist.json")):
            self.create_learned_cache(model_path=model_path, cache_root="Preprocessing/multilinguality")
        if create_oracle:
            if not os.path.exists(os.path.join(self.cache_root, "lang_1_to_lang_2_to_oracle_dist.json")):
                if not model_path:
                    raise ValueError("model_path is required for creating oracle cache.")
                self.create_oracle_cache(model_path=args.model_path, cache_root="Preprocessing/multilinguality")
        print("All required cache files exist.")


if __name__ == '__main__':
    default_model_path = hf_hub_download(repo_id="Flux9665/ToucanTTS", filename="ToucanTTS.pt")
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", "-m", type=str, default=default_model_path, help="model path that should be used for creating oracle lang emb distance cache")
    args = parser.parse_args()
    cc = CacheCreator()
    cc.create_required_files(args.model_path, create_oracle=True)
