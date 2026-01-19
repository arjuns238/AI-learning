import pandas as pd

splits = {'train': 'manim_sft_dataset_train_v2.parquet', 'test': 'manim_sft_dataset_test_v2.parquet', 'all': 'manim_sft_dataset_v2.parquet'}
df = pd.read_parquet("hf://datasets/SuienR/ManimBench-v1/" + splits["train"])
print(df.head())
print(f"Total training samples: {len(df)}")