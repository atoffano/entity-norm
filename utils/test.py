import json
config = {}

# config['lightweight'] = {'dataset' : 'ncbi', 'sentence_length': 20, 'character_length' : 100, 'batch_size' : 64, 'filters' : 32, 'kernel_sizes' : '1,2,3', 'dropout' : 0.1, 'char_dim' : 128, 'word_embed_dim' : 200, 'learning_rate' : 0.001, 'decay_rate': 0.05, 'char_rnn_dim' : 64, 'hinge' : 0.1, 'topk_candidates' : 20, 'alpha' : 0.0, 'voting_k' : 8, 'context_sentence_length' : 100, 'context_rnn_dim' : 32, 'epochs' : 30, 'seed_value' : None, 'steps_per_epoch' : 500, 'random_init' : False, 'add_context' : False, 'add_coherence' : False, 'add_prior' : False}
# config['BioSyn'] = {'model_name_or_path' : '', 'train_dictionary_path' : '', 'train_dir' : '', 'output_dir' : '', 'max_length' : 25, 'seed' : '0', 'use_cuda' : True, 'draft' : '', 'topk' : '20', 'learning_rate' : 0.0001, 'weight_decay' : 0.01, 'train_batch_size' : 16, 'epoch' : 10, 'initial_sparse_weight' : 0, 'dense_ratio' : 0.5, 'save_checkpoint_all' : True}
# # with open('/home/atoffano/montages_reseau/home_maiage/menneb/entity-norm/config.json', 'w') as f:
# #     json.dump(config, f, indent=2)

#     # Loads all models parameters
# params = json.load(open('/home/atoffano/montages_reseau/home_maiage/menneb/entity-norm/config.json', 'r'))
# print(params['BioSyn'])

print(f'a{"z" if 1 == 1 else "e"}')