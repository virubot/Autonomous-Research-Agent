"""End-to-end test: generate IEEE and APA PDFs with publication-quality content."""
import sys
sys.path.insert(0, '.')

from backend.pdf_generator import generate_pdf

sample = {
    "title": "Adaptive Deep Reinforcement Learning for Personalized Education: A Multi-Agent Framework",
    "authors": ["Viren K. Patel", "Ananya S. Sharma"],
    "affiliation": "Department of Computer Science, Indian Institute of Technology, Mumbai, India",
    "contact_email": "viren.patel@iit.ac.in",
    "abstract": (
        "The rapid proliferation of online learning platforms has created an unprecedented demand for "
        "personalized educational experiences that adapt to individual learner characteristics, preferences, "
        "and knowledge states. Traditional recommendation systems, while effective in e-commerce domains, "
        "often fail to capture the pedagogical nuances inherent in educational content sequencing, such as "
        "prerequisite dependencies, cognitive load balancing, and learning objective alignment. This paper "
        "presents AdaptiveRL-Edu, a novel multi-agent deep reinforcement learning framework that formulates "
        "personalized curriculum optimization as a cooperative Markov decision process. Our architecture "
        "employs three specialized agents: a Knowledge State Estimator based on deep knowledge tracing with "
        "attention mechanisms, a Content Sequencer utilizing proximal policy optimization with curriculum-aware "
        "reward shaping, and a Difficulty Calibrator implementing contextual bandits for real-time assessment "
        "adaptation. Extensive experiments on three large-scale educational datasets---EdNet (131M interactions), "
        "ASSISTments (2.7M records), and a proprietary MOOC dataset (450K learners)---demonstrate that "
        "AdaptiveRL-Edu achieves a 23.7 percent improvement in learning gain metrics and a 31.2 percent reduction "
        "in time-to-mastery compared to state-of-the-art baselines including DKT-DSR, CSEAL, and HRL-Rec. "
        "Furthermore, qualitative analysis reveals that our framework produces pedagogically coherent learning "
        "paths that align with established instructional design principles."
    ),
    "keywords": [
        "deep reinforcement learning", "personalized education",
        "adaptive learning", "knowledge tracing", "curriculum optimization"
    ],
    "sections": [
        {
            "title": "Introduction",
            "content": [
                "The democratization of education through massive open online courses (MOOCs) and intelligent tutoring systems (ITS) has fundamentally transformed how millions of learners worldwide acquire knowledge and skills. Platforms such as Coursera, edX, and Khan Academy collectively serve over 220 million registered learners, offering access to university-level content across diverse disciplines. However, the one-size-fits-all approach that characterizes most existing platforms fails to account for the substantial heterogeneity in learner backgrounds, cognitive abilities, and motivational states. Research in educational psychology consistently demonstrates that personalized instruction, which adapts content presentation, sequencing, and difficulty to individual learner characteristics, yields significantly superior learning outcomes compared to standardized curricula.",
                "The challenge of automated curriculum personalization can be naturally formulated as a sequential decision-making problem under uncertainty, where an intelligent agent must select appropriate learning activities for each student based on their evolving knowledge state. Reinforcement learning provides a principled framework for this formulation, as it enables agents to learn optimal policies through interaction with the learning environment without requiring explicit models of student cognition. Recent advances in deep reinforcement learning have further expanded the applicability of RL methods to high-dimensional state spaces characteristic of educational settings, where student knowledge states are represented as continuous vectors over hundreds of knowledge components.",
                "Despite promising initial results, existing RL-based educational recommendation systems suffer from several critical limitations. First, most approaches employ single-agent architectures that attempt to jointly optimize content selection, difficulty calibration, and knowledge assessment within a monolithic policy, leading to sample inefficiency and unstable training dynamics. Second, reward function design remains ad hoc, with many systems relying on simplistic binary correct/incorrect signals that fail to capture the multidimensional nature of learning progress. Third, the cold-start problem is particularly severe in educational contexts, where initial student assessments are often unreliable and exploration costs are high due to the potential for learner frustration and disengagement.",
                "To address these challenges, this paper introduces AdaptiveRL-Edu, a cooperative multi-agent deep reinforcement learning framework designed specifically for personalized curriculum optimization. Our key insight is that the curriculum personalization problem naturally decomposes into three interconnected sub-problems---knowledge state estimation, content sequencing, and difficulty calibration---each of which can be addressed by a specialized agent while maintaining coherent system-level behavior through a shared communication protocol.",
                "The principal contributions of this work are fourfold. First, we propose a novel multi-agent architecture that decomposes curriculum optimization into cooperating specialized agents, achieving better sample efficiency and more stable training compared to monolithic alternatives. Second, we introduce a curriculum-aware reward shaping mechanism that incorporates pedagogical principles including zone of proximal development theory and spaced repetition into the RL optimization objective. Third, we develop an attention-based deep knowledge tracing model that provides more accurate and interpretable estimates of student knowledge states. Fourth, we conduct extensive experiments on three large-scale datasets, demonstrating substantial improvements over existing baselines across multiple evaluation metrics."
            ]
        },
        {
            "title": "Related Work",
            "content": [
                "Knowledge tracing, the problem of modeling student knowledge states from interaction data, has been studied extensively in the intelligent tutoring systems community. Corbett and Anderson introduced Bayesian Knowledge Tracing (BKT) in 1994, which models each knowledge component as a binary latent variable with transition probabilities governing learning and forgetting. While BKT remains widely used due to its interpretability, its assumption of binary knowledge states and independence between knowledge components limits its expressiveness. Deep Knowledge Tracing (DKT), introduced by Piech et al. in 2015, addressed these limitations by employing recurrent neural networks to model student knowledge as continuous hidden states, achieving significant improvements on next-response prediction tasks across multiple educational datasets.",
                "Subsequent work has refined the DKT framework in several directions. Zhang et al. proposed Dynamic Key-Value Memory Networks for Knowledge Tracing (DKVMN), which explicitly represents knowledge concepts as key-value pairs in an external memory structure, enabling more interpretable knowledge state representations. Ghosh et al. introduced AKT (Attentive Knowledge Tracing), which leverages self-attention mechanisms to capture long-range dependencies in student interaction sequences and achieves state-of-the-art performance on the ASSISTments and EdNet benchmarks. More recently, Shin et al. developed SAINT+, which employs a transformer encoder-decoder architecture with elapsed time and lag time features, demonstrating that temporal information significantly improves prediction accuracy.",
                "The application of reinforcement learning to educational content recommendation has gained substantial traction in recent years. Early work by Iglesias et al. formulated tutoring strategy selection as a Markov decision process and applied tabular Q-learning to optimize feedback timing in a physics tutoring system. Doroudi et al. provided a comprehensive survey of RL applications in education, identifying key challenges including reward specification, state representation, and evaluation methodology. More recently, Shi et al. proposed CSEAL (Contextual Student Engagement-Aware Learning), which uses contextual bandits to adapt content difficulty based on real-time engagement signals, achieving a 15 percent improvement in completion rates on a MOOC platform.",
                "Multi-agent reinforcement learning (MARL) has been applied to various domains including autonomous driving, robotic manipulation, and strategic game playing, but its application to educational personalization remains largely unexplored. Lowe et al. introduced MADDPG (Multi-Agent Deep Deterministic Policy Gradient), which enables decentralized execution with centralized training in cooperative and competitive settings. Rashid et al. proposed QMIX, a value decomposition method that represents joint action-values as a monotonic combination of per-agent utilities, enabling efficient cooperative learning. Our work builds on these MARL foundations while introducing domain-specific innovations tailored to the educational recommendation problem.",
                "Curriculum learning, originally proposed by Bengio et al. in the context of machine learning model training, bears conceptual similarities to our work but operates in a fundamentally different setting. While curriculum learning for ML focuses on ordering training examples to improve model convergence, our framework optimizes the sequence of educational content presented to human learners, requiring explicit modeling of cognitive processes, prerequisite structures, and motivational dynamics. Recent work by Graves et al. on automated curriculum learning with multi-armed bandits provides a bridge between these two perspectives, suggesting that adaptive sequencing strategies can yield benefits in both machine and human learning contexts."
            ]
        },
        {
            "title": "Proposed Methodology",
            "content": [
                "The AdaptiveRL-Edu framework formulates personalized curriculum optimization as a cooperative multi-agent Markov decision process (Dec-POMDP). We define the environment as a tuple (S, A_1, A_2, A_3, T, R, O, gamma), where S represents the joint state space comprising student knowledge states, content features, and session context; A_i denotes the action space of each agent; T defines the state transition dynamics; R is the shared reward function; O represents the observation function mapping states to per-agent observations; and gamma is the discount factor set to 0.99 in all experiments.",
                "The Knowledge State Estimator (KSE) agent maintains a probabilistic representation of each student's mastery level across K knowledge components. We extend the AKT architecture by incorporating a hierarchical attention mechanism that operates at both the interaction level and the concept level. Given a sequence of student interactions x_1, ..., x_t, each represented as a tuple (concept_id, response, elapsed_time, attempt_count), the KSE produces a knowledge state vector h_t in R^K through a multi-head self-attention encoder followed by a concept-level aggregation layer. The attention weights provide interpretable information about which prior interactions are most relevant for estimating current mastery, enabling instructors to understand and validate the system's knowledge state estimates.",
                "The Content Sequencer (CS) agent is responsible for selecting the next learning activity from a candidate pool based on the current knowledge state estimate and the overarching learning objectives. We implement the CS using Proximal Policy Optimization (PPO) with a curriculum-aware reward shaping function. The action space consists of selecting one of N candidate activities, where each activity is characterized by a feature vector encoding its topic coverage, difficulty level, estimated completion time, prerequisite requirements, and pedagogical type (e.g., video lecture, practice problem, interactive simulation). The policy network is a 4-layer MLP with 256 hidden units per layer and ReLU activations, taking as input the concatenation of the knowledge state vector, the learning objective embedding, and the session context features.",
                "The Difficulty Calibrator (DC) agent adjusts the difficulty parameters of the selected activity to match the student's current zone of proximal development. We implement the DC using a contextual bandit framework with Thompson sampling, where the context vector consists of the student's estimated mastery level on relevant knowledge components, their historical performance at different difficulty levels, and the time elapsed since the last interaction with the target concept. The DC outputs a continuous difficulty scaling factor in [0.5, 1.5] that modulates the complexity of the selected activity through parameterized content generation templates.",
                "Inter-agent communication is facilitated through a shared message-passing protocol inspired by CommNet. At each decision step, each agent broadcasts a fixed-size message vector (d=64) that encodes its current state assessment and proposed action. These messages are aggregated through a learnable attention mechanism and incorporated into each agent's observation, enabling coordinated decision-making without explicit centralized control. The training procedure follows a centralized training with decentralized execution (CTDE) paradigm, where a centralized critic has access to all agents' observations and actions during training, while each agent's policy operates only on its local observation and received messages during deployment."
            ]
        },
        {
            "title": "Experimental Setup and Results",
            "content": [
                "We evaluate AdaptiveRL-Edu on three large-scale educational datasets spanning different domains and interaction modalities. EdNet, collected from the Santa platform for TOEIC preparation, contains 131 million interactions from 784,309 students across 13,169 questions organized into 188 knowledge components. ASSISTments, a widely-used benchmark from the ASSISTments online tutoring platform, comprises 2.7 million interactions from 4,163 students on 26,688 items covering middle school mathematics. Our proprietary MOOC dataset, collected from a major Indian online learning platform, includes 450,000 learners interacting with 12,500 learning activities across 340 knowledge components in computer science and data science courses, totaling over 89 million interaction records.",
                "We compare AdaptiveRL-Edu against seven baseline methods representing the state of the art in educational recommendation. These include: (1) Random selection, (2) Most-Popular recommendation, (3) BKT-based sequencing, (4) DKT with greedy content selection (DKT-Greedy), (5) CSEAL contextual bandit approach, (6) HRL-Rec hierarchical RL recommendation, and (7) DKT-DSR, which combines deep knowledge tracing with deep successor representations. All baselines are implemented using their original published codebases and hyperparameters, with minor adaptations for compatibility with our evaluation framework. For fairness, all methods use the same train/validation/test splits with 70/10/20 ratios applied at the student level.",
                "Our primary evaluation metrics capture both short-term prediction accuracy and long-term learning effectiveness. For knowledge state estimation quality, we report AUC (Area Under the ROC Curve) and RMSE on next-response prediction. For curriculum optimization, we measure Learning Gain (LG), defined as the normalized difference between pre-test and post-test scores; Time-to-Mastery (TTM), measured as the number of interactions required to achieve 80 percent mastery on target knowledge components; and Curriculum Coherence Score (CCS), a novel metric we introduce that quantifies the pedagogical validity of recommended sequences based on prerequisite graph traversal patterns.",
                "Table I summarizes the main experimental results. AdaptiveRL-Edu achieves the highest performance across all metrics and datasets. On EdNet, our framework achieves an AUC of 0.847 (compared to 0.812 for the best baseline DKT-DSR), a learning gain improvement of 23.7 percent over random sequencing, and a time-to-mastery reduction of 31.2 percent compared to DKT-Greedy. On ASSISTments, we observe an AUC of 0.831, surpassing SAINT+ (0.819) and AKT (0.814). The improvements on the MOOC dataset are particularly pronounced, with a 27.4 percent learning gain improvement and 34.8 percent TTM reduction, which we attribute to the richer interaction modalities (videos, quizzes, coding exercises) that benefit from our multi-agent decomposition approach.",
                "Ablation studies reveal that each component of our framework contributes meaningfully to overall performance. Removing the inter-agent communication protocol results in a 4.2 percent AUC decrease on EdNet, confirming the importance of coordinated decision-making. Replacing the attention-based KSE with standard DKT reduces learning gain by 8.3 percent, demonstrating the value of our enhanced knowledge state estimation. Using a fixed difficulty level instead of the DC agent increases TTM by 18.7 percent, highlighting the critical role of adaptive difficulty calibration. Finally, substituting our curriculum-aware reward with a simple binary reward (correct/incorrect) degrades CCS by 22.1 percent, validating our pedagogically-grounded reward design."
            ]
        },
        {
            "title": "Discussion",
            "content": [
                "The experimental results demonstrate that decomposing curriculum personalization into cooperating specialized agents yields substantial benefits over monolithic approaches. The 23.7 percent improvement in learning gain over the strongest baseline represents a practically significant advancement, corresponding to approximately 1.4 standard deviations in educational effect size terms. This improvement is particularly noteworthy given that it is achieved without any increase in the total amount of content consumed by learners, suggesting that our framework's primary contribution is in optimizing the sequencing and difficulty calibration of existing educational materials.",
                "The multi-agent architecture provides several advantages beyond raw performance improvements. First, the modular design enables independent updates to individual agents without retraining the entire system, which is crucial for production deployment where content libraries are frequently updated. Second, the attention-based knowledge state estimator produces interpretable attention weights that can be visualized for instructors, enabling them to understand and validate the system's assessment of student knowledge. Third, the separation of content sequencing and difficulty calibration allows for fine-grained control over the pedagogical strategy, with the possibility of incorporating instructor preferences or institutional constraints into individual agents.",
                "Several limitations of our current approach merit discussion. The cooperative MARL formulation assumes that all three agents share the same reward function, which may not perfectly capture real-world scenarios where assessment accuracy and learning engagement may sometimes conflict. Our evaluation relies on standardized pre-test and post-test measurements, which may not fully capture deeper learning outcomes such as transfer ability and long-term retention. Additionally, our framework requires substantial interaction data for training (minimum 50,000 student trajectories for stable convergence), which may limit its applicability in smaller educational settings or for newly launched courses with limited historical data.",
                "The cold-start problem, while partially addressed by our attention-based KSE which can leverage similarities between new and existing students, remains a significant challenge. Our current approach uses a pre-trained knowledge state estimator on the full dataset and fine-tunes it with limited interactions from new students, achieving reasonable performance after approximately 20 interactions. However, the initial 20-interaction period may involve sub-optimal recommendations, potentially affecting student engagement. Future work should explore meta-learning approaches that can rapidly adapt to new students with minimal data.",
                "Comparing our results with concurrent work in the field, we note that the improvements achieved by AdaptiveRL-Edu are consistent with recent theoretical analyses suggesting that multi-agent decomposition can improve sample efficiency in structured cooperative tasks. The 31.2 percent reduction in time-to-mastery aligns with findings from educational psychology research on the benefits of adaptive difficulty calibration, specifically Vygotsky's zone of proximal development theory, which posits that learning is most efficient when tasks are slightly beyond a learner's current ability level."
            ]
        },
        {
            "title": "Conclusion",
            "content": [
                "This paper presented AdaptiveRL-Edu, a cooperative multi-agent deep reinforcement learning framework for personalized curriculum optimization in online learning environments. By decomposing the curriculum personalization problem into three specialized agents responsible for knowledge state estimation, content sequencing, and difficulty calibration, our framework achieves state-of-the-art performance on three large-scale educational datasets. The experimental results demonstrate a 23.7 percent improvement in learning gain and a 31.2 percent reduction in time-to-mastery compared to existing baselines, while producing pedagogically coherent learning paths as measured by our novel Curriculum Coherence Score.",
                "The multi-agent architecture provides several practical advantages for production deployment, including modularity, interpretability, and fine-grained control over pedagogical strategies. Our attention-based knowledge state estimator produces interpretable attention weights that enable instructors to understand and validate the system's assessment of student knowledge, addressing a critical requirement for real-world adoption of AI-driven educational tools.",
                "The broader implications of this work extend beyond the specific technical contributions. As AI-powered educational tools become increasingly prevalent, it is essential that they incorporate established pedagogical principles rather than purely optimizing for engagement metrics. Our curriculum-aware reward shaping mechanism provides a principled approach for encoding pedagogical knowledge into RL optimization objectives, bridging the gap between machine learning research and educational practice.",
                "We believe that the multi-agent decomposition paradigm proposed in this work has significant potential for application to other complex personalization problems that involve multiple interacting decision dimensions, such as healthcare treatment planning, adaptive user interface design, and personalized content creation."
            ]
        },
        {
            "title": "Future Work",
            "content": [
                "Several promising directions for future research emerge from this work. First, we plan to extend the framework to support collaborative learning scenarios, where the curriculum optimization must account for interactions between learners working in groups. This requires modeling social dynamics, peer learning effects, and group composition optimization, which can be naturally formulated as additional agents within our multi-agent framework. Preliminary experiments with pair programming exercises in our MOOC dataset suggest that collaborative learning paths can improve engagement by up to 18 percent compared to individual learning.",
                "Second, we intend to investigate the integration of multimodal learning analytics, including video gaze tracking, keystroke dynamics, and natural language processing of student-generated text, into the knowledge state estimation pipeline. These additional modalities could provide richer signals about student engagement, confusion, and learning strategies, potentially enabling more nuanced and responsive curriculum adaptation. Recent advances in multimodal transformers provide a promising architectural foundation for this integration.",
                "Third, the development of more sophisticated reward functions that capture long-term learning outcomes, including knowledge retention, transfer ability, and metacognitive skills development, represents an important research frontier. We plan to explore inverse reinforcement learning approaches that can infer reward functions from expert instructor demonstrations, potentially capturing tacit pedagogical knowledge that is difficult to formalize explicitly.",
                "Finally, we aim to conduct longitudinal controlled studies in real classroom settings to validate the ecological validity of our framework and measure its impact on authentic learning outcomes over extended periods. While our current evaluation demonstrates strong performance on standardized metrics, real-world educational impact requires careful assessment of learner satisfaction, self-regulated learning development, and long-term knowledge retention that can only be captured through sustained deployment and rigorous experimental design."
            ]
        },
    ],
    "citations": [
        "[S1] EdNet Dataset (Choi et al., 2020)",
        "[S2] ASSISTments (Feng et al., 2009)",
        "[S3] DKT (Piech et al., 2015)",
        "[S4] PPO (Schulman et al., 2017)",
    ],
    "references": [
        {"text": 'C. Piech et al., "Deep Knowledge Tracing," in Advances in Neural Information Processing Systems, vol. 28, pp. 505-513, 2015.'},
        {"text": 'Y. Choi et al., "EdNet: A Large-Scale Hierarchical Dataset in Education," in Proc. Int. Conf. Artificial Intelligence in Education, pp. 69-73, 2020.'},
        {"text": 'J. Zhang et al., "Dynamic Key-Value Memory Networks for Knowledge Tracing," in Proc. 26th Int. Conf. World Wide Web, pp. 765-774, 2017.'},
        {"text": 'A. Ghosh, N. Heffernan, and A. Lan, "Context-Aware Attentive Knowledge Tracing," in Proc. ACM SIGKDD Int. Conf. Knowledge Discovery and Data Mining, pp. 2330-2339, 2020.'},
        {"text": 'D. Shin, Y. Shim, H. Yu, S. Lee, B. Kim, and Y. Choi, "SAINT+: Integrating Temporal Features for EdNet Correctness Prediction," in Proc. LAK, pp. 490-496, 2021.'},
        {"text": 'J. Schulman, F. Wolski, P. Dhariwal, A. Radford, and O. Klimov, "Proximal Policy Optimization Algorithms," arXiv preprint arXiv:1707.06347, 2017.'},
        {"text": 'S. Doroudi, V. Aleven, and E. Brunskill, "Where\'s the Reward? A Review of Reinforcement Learning for Instructional Sequencing," Int. J. Artificial Intelligence in Education, vol. 29, no. 4, pp. 568-620, 2019.'},
        {"text": 'D. Shi et al., "CSEAL: Contextual Student Engagement-Aware Learning for Adaptive Content Recommendation," in Proc. AAAI Conf. Artificial Intelligence, pp. 13210-13218, 2023.'},
        {"text": 'R. Lowe et al., "Multi-Agent Actor-Critic for Mixed Cooperative-Competitive Environments," in Advances in Neural Information Processing Systems, vol. 30, pp. 6379-6390, 2017.'},
        {"text": 'T. Rashid et al., "QMIX: Monotonic Value Function Factorisation for Deep Multi-Agent Reinforcement Learning," in Proc. Int. Conf. Machine Learning, pp. 4295-4304, 2018.'},
        {"text": 'Y. Bengio, J. Louradour, R. Collobert, and J. Weston, "Curriculum Learning," in Proc. 26th Int. Conf. Machine Learning, pp. 41-48, 2009.'},
        {"text": 'A. Graves, M. Bellemare, J. Menick, R. Munos, and K. Kavukcuoglu, "Automated Curriculum Learning for Neural Networks," in Proc. Int. Conf. Machine Learning, pp. 1311-1320, 2017.'},
        {"text": 'A. T. Corbett and J. R. Anderson, "Knowledge Tracing: Modeling the Acquisition of Procedural Knowledge," User Modeling and User-Adapted Interaction, vol. 4, no. 4, pp. 253-278, 1994.'},
        {"text": 'M. Feng, N. Heffernan, and K. Koedinger, "Addressing the Assessment Challenge with an Online System That Tutors as It Assesses," User Modeling and User-Adapted Interaction, vol. 19, no. 3, pp. 243-266, 2009.'},
        {"text": 'S. Sukhbaatar, A. Szlam, and R. Fergus, "Learning Multiagent Communication with Backpropagation," in Advances in Neural Information Processing Systems, vol. 29, pp. 2244-2252, 2016.'},
    ],
}

print("=" * 60)
print("Testing IEEE PDF generation...")
print("=" * 60)
try:
    path = generate_pdf(sample, format_type="ieee")
    print(f"IEEE SUCCESS: {path}")
except Exception as e:
    print(f"IEEE FAILED: {e}")

print()
print("=" * 60)
print("Testing APA PDF generation...")
print("=" * 60)
try:
    path = generate_pdf(sample, format_type="apa")
    print(f"APA SUCCESS: {path}")
except Exception as e:
    print(f"APA FAILED: {e}")

print()
print("=" * 60)
print("Testing ACM PDF generation...")
print("=" * 60)
try:
    path = generate_pdf(sample, format_type="acm")
    print(f"ACM SUCCESS: {path}")
except Exception as e:
    print(f"ACM FAILED: {e}")
