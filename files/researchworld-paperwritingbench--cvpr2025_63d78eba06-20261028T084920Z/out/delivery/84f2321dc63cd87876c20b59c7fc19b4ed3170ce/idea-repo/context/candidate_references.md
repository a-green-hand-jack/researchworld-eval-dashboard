# Verified literature (before 2024-11) for related work and references.bib

Checked against OpenAlex / Crossref / arXiv + Semantic Scholar (author lists checked where the table says so). Same content as `context/candidate_references.md` in `world/idea-repo`.

## One line per paper

| Key | What it establishes (use only for this) | Verified |
|---|---|---|
| cao2015towards | Introduces "machine unlearning": make a system forget a training sample efficiently without full retraining | OpenAlex, DOI |
| bourtoule2021machine | SISA: exact unlearning by sharded/sliced retraining; requires the data to be kept | Crossref, 8 authors |
| ginart2019making | Data-deletion problem formalised for ML (k-means), efficient deletion | OpenAlex |
| koh2017understanding | Influence functions via Hessian-inverse-vector products to estimate effect of removing a training point | OpenAlex |
| guo2020certified | Certified removal: one Newton-type update with the Hessian of the remaining data plus noise, for (regularised) linear models; needs the data | OpenAlex |
| sekhari2021remember | Algorithms and generalisation guarantees for unlearning with Hessian-based update; limited access to the data | OpenAlex |
| neel2021descent | Gradient-based deletion for convex models with guarantees | OpenAlex (arXiv 2020; ALT 2021 venue from my knowledge, confirm) |
| golatkar2020eternal | Fisher-based scrubbing of weights on deep networks; also the standard source of the Random-Labels/ NegGrad-style fine-tuning baselines in later work (attribution of baselines is my reading, hedge) | Crossref |
| golatkar2020forgetting | Scrubbing with NTK for black-box observation | Crossref |
| golatkar2021mixed | Mixed-linear (linearised last layers) networks, which make forgetting tractable; the "mixed linear network" setting of the log | OpenAlex, 5 authors |
| chundawat2023zero | Zero-shot (no data) class/sample unlearning with synthetic data / error minimisation-maximisation | Crossref |
| tarun2023fast | Error-maximising noise + repair for class unlearning without the original data | Crossref |
| foster2024information | JiT: Lipschitz-regularisation zero-shot unlearning (first circulated as "Zero-shot Machine Unlearning at Scale via Lipschitz Regularization") | arXiv page, Semantic Scholar, TMLR |
| foster2024fast | SSD: weight dampening using Fisher information, no retraining, needs the retain data statistics | Crossref |
| cha2024learning | Instance-wise unlearning for pre-trained classifiers via adversarial examples + weight importance: my reading of the log's "Adversarial" baseline | OpenAlex, 6 authors |
| kurmanji2023towards | SCRUB; also sets up the unlearning vs. MIA evaluation | OpenAlex |
| chen2023boundary | Boundary shifting unlearning (CVPR 2023) | Crossref |
| graves2021amnesiac | Amnesiac ML: undo updates from batches containing the data; Random-Labels-type related work | OpenAlex |
| shokri2017membership | Membership inference attacks; MIA score of ~50% = indistinguishable | OpenAlex |
| xu2023machine | Survey of machine unlearning | Crossref |
| krizhevsky2009learning | CIFAR-10/100 | well-known tech report (not indexed; confirm fields) |
| griffin2007caltech | Caltech-256 | OpenAlex |
| khosla2011novel | Stanford Dogs | NOT index-verified (OpenAlex/Crossref return nothing); real FGVC workshop paper, confirm before use |
| he2016deep | ResNet | Crossref |
| deng2009imagenet | ImageNet pre-training | Crossref |
| gdpr2016 | GDPR (right to erasure) | official-text citation, not an indexed paper |

Notes: NegGrad has no single canonical source (gradient ascent on the forget set; appears in Golatkar 2020 / Kurmanji 2023 style baselines): either cite those as "e.g." or describe it without a citation. Do not cite anything after 2024-11. Cite nothing from outside this list without verifying it.

## BibTeX

```bibtex
@inproceedings{cao2015towards,
  title={Towards Making Systems Forget with Machine Unlearning},
  author={Cao, Yinzhi and Yang, Junfeng},
  booktitle={IEEE Symposium on Security and Privacy},
  year={2015},
  doi={10.1109/SP.2015.35}
}
@inproceedings{bourtoule2021machine,
  title={Machine Unlearning},
  author={Bourtoule, Lucas and Chandrasekaran, Varun and Choquette-Choo, Christopher A. and Jia, Hengrui and Travers, Adelin and Zhang, Baiwu and Lie, David and Papernot, Nicolas},
  booktitle={IEEE Symposium on Security and Privacy},
  year={2021},
  doi={10.1109/SP40001.2021.00019}
}
@inproceedings{ginart2019making,
  title={Making {AI} Forget You: Data Deletion in Machine Learning},
  author={Ginart, Antonio A. and Guan, Melody Y. and Valiant, Gregory and Zou, James},
  booktitle={Advances in Neural Information Processing Systems},
  year={2019}
}
@inproceedings{koh2017understanding,
  title={Understanding Black-box Predictions via Influence Functions},
  author={Koh, Pang Wei and Liang, Percy},
  booktitle={International Conference on Machine Learning},
  year={2017}
}
@inproceedings{guo2020certified,
  title={Certified Data Removal from Machine Learning Models},
  author={Guo, Chuan and Goldstein, Tom and Hannun, Awni and van der Maaten, Laurens},
  booktitle={International Conference on Machine Learning},
  year={2020}
}
@inproceedings{sekhari2021remember,
  title={Remember What You Want to Forget: Algorithms for Machine Unlearning},
  author={Sekhari, Ayush and Acharya, Jayadev and Kamath, Gautam and Suresh, Ananda Theertha},
  booktitle={Advances in Neural Information Processing Systems},
  year={2021}
}
@inproceedings{neel2021descent,
  title={Descent-to-Delete: Gradient-Based Methods for Machine Unlearning},
  author={Neel, Seth and Roth, Aaron and Sharifi-Malvajerdi, Saeed},
  booktitle={Algorithmic Learning Theory},
  year={2021}
}
@inproceedings{golatkar2020eternal,
  title={Eternal Sunshine of the Spotless Net: Selective Forgetting in Deep Networks},
  author={Golatkar, Aditya and Achille, Alessandro and Soatto, Stefano},
  booktitle={IEEE/CVF Conference on Computer Vision and Pattern Recognition},
  year={2020},
  doi={10.1109/CVPR42600.2020.00932}
}
@inproceedings{golatkar2020forgetting,
  title={Forgetting Outside the Box: Scrubbing Deep Networks of Information Accessible from Input-Output Observations},
  author={Golatkar, Aditya and Achille, Alessandro and Soatto, Stefano},
  booktitle={European Conference on Computer Vision},
  year={2020},
  doi={10.1007/978-3-030-58526-6_23}
}
@inproceedings{golatkar2021mixed,
  title={Mixed-Privacy Forgetting in Deep Networks},
  author={Golatkar, Aditya and Achille, Alessandro and Ravichandran, Avinash and Polito, Marzia and Soatto, Stefano},
  booktitle={IEEE/CVF Conference on Computer Vision and Pattern Recognition},
  year={2021},
  doi={10.1109/CVPR46437.2021.00085}
}
@article{chundawat2023zero,
  title={Zero-Shot Machine Unlearning},
  author={Chundawat, Vikram S. and Tarun, Ayush K. and Mandal, Murari and Kankanhalli, Mohan},
  journal={IEEE Transactions on Information Forensics and Security},
  year={2023},
  doi={10.1109/TIFS.2023.3265506}
}
@article{tarun2023fast,
  title={Fast Yet Effective Machine Unlearning},
  author={Tarun, Ayush K. and Chundawat, Vikram S. and Mandal, Murari and Kankanhalli, Mohan},
  journal={IEEE Transactions on Neural Networks and Learning Systems},
  year={2023},
  doi={10.1109/TNNLS.2023.3266233}
}
@article{foster2024information,
  title={An Information Theoretic Approach to Machine Unlearning},
  author={Foster, Jack and Fogarty, Kyle and Schoepf, Stefan and Dugue, Zack and {\"O}ztireli, Cengiz and Brintrup, Alexandra},
  journal={Transactions on Machine Learning Research},
  year={2024},
  note={arXiv:2402.01401; first circulated as ``Zero-shot Machine Unlearning at Scale via Lipschitz Regularization'' (JiT)}
}
@inproceedings{foster2024fast,
  title={Fast Machine Unlearning without Retraining through Selective Synaptic Dampening},
  author={Foster, Jack and Schoepf, Stefan and Brintrup, Alexandra},
  booktitle={AAAI Conference on Artificial Intelligence},
  year={2024},
  doi={10.1609/aaai.v38i11.29092}
}
@inproceedings{cha2024learning,
  title={Learning to Unlearn: Instance-wise Unlearning for Pre-trained Classifiers},
  author={Cha, Sungmin and Cho, Sungjun and Hwang, Dasol and Lee, Honglak and Moon, Taesup and Lee, Moontae},
  booktitle={AAAI Conference on Artificial Intelligence},
  year={2024},
  doi={10.1609/aaai.v38i10.28996}
}
@inproceedings{kurmanji2023towards,
  title={Towards Unbounded Machine Unlearning},
  author={Kurmanji, Meghdad and Triantafillou, Peter and Hayes, Jamie and Triantafillou, Eleni},
  booktitle={Advances in Neural Information Processing Systems},
  year={2023}
}
@inproceedings{chen2023boundary,
  title={Boundary Unlearning: Rapid Forgetting of Deep Networks via Shifting the Decision Boundary},
  author={Chen, Min and Gao, Weizhuo and Liu, Gaoyang and Peng, Kai and Wang, Chen},
  booktitle={IEEE/CVF Conference on Computer Vision and Pattern Recognition},
  year={2023},
  doi={10.1109/CVPR52729.2023.00750}
}
@inproceedings{graves2021amnesiac,
  title={Amnesiac Machine Learning},
  author={Graves, Laura and Nagisetty, Vineel and Ganesh, Vijay},
  booktitle={AAAI Conference on Artificial Intelligence},
  year={2021},
  doi={10.1609/aaai.v35i13.17371}
}
@inproceedings{shokri2017membership,
  title={Membership Inference Attacks Against Machine Learning Models},
  author={Shokri, Reza and Stronati, Marco and Song, Congzheng and Shmatikov, Vitaly},
  booktitle={IEEE Symposium on Security and Privacy},
  year={2017},
  doi={10.1109/SP.2017.41}
}
@article{xu2023machine,
  title={Machine Unlearning: A Survey},
  author={Xu, Heng and Zhu, Tianqing and Zhang, Lefeng and Zhou, Wanlei and Yu, Philip S.},
  journal={ACM Computing Surveys},
  year={2023},
  doi={10.1145/3603620}
}
@techreport{krizhevsky2009learning,
  title={Learning Multiple Layers of Features from Tiny Images},
  author={Krizhevsky, Alex},
  institution={University of Toronto},
  year={2009}
}
@techreport{griffin2007caltech,
  title={Caltech-256 Object Category Dataset},
  author={Griffin, Gregory and Holub, Alex and Perona, Pietro},
  institution={California Institute of Technology},
  year={2007}
}
@inproceedings{khosla2011novel,
  title={Novel Dataset for Fine-Grained Image Categorization},
  author={Khosla, Aditya and Jayadevaprakash, Nityananda and Yao, Bangpeng and Fei-Fei, Li},
  booktitle={CVPR Workshop on Fine-Grained Visual Categorization},
  year={2011}
}
@inproceedings{he2016deep,
  title={Deep Residual Learning for Image Recognition},
  author={He, Kaiming and Zhang, Xiangyu and Ren, Shaoqing and Sun, Jian},
  booktitle={IEEE/CVF Conference on Computer Vision and Pattern Recognition},
  year={2016},
  doi={10.1109/CVPR.2016.90}
}
@inproceedings{deng2009imagenet,
  title={{ImageNet}: A Large-Scale Hierarchical Image Database},
  author={Deng, Jia and Dong, Wei and Socher, Richard and Li, Li-Jia and Li, Kai and Fei-Fei, Li},
  booktitle={IEEE Conference on Computer Vision and Pattern Recognition},
  year={2009},
  doi={10.1109/CVPR.2009.5206848}
}
@misc{gdpr2016,
  title={Regulation ({EU}) 2016/679 of the {European Parliament} and of the {Council} (General Data Protection Regulation)},
  author={{European Parliament and Council of the European Union}},
  howpublished={Official Journal of the European Union, L 119},
  year={2016}
}
```
