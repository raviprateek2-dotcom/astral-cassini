import { useJobStore } from "@/store/useJobStore";

describe("useJobStore", () => {
  beforeEach(() => {
    useJobStore.setState({
      currentJob: null,
      jobsList: [],
      loading: false,
      error: null,
    });
  });

  it("merges socket state into current job", () => {
    useJobStore.setState({
      currentJob: {
        job_id: "job-1",
        job_title: "QA Engineer",
        department: "QA",
        current_stage: "sourcing",
        created_at: new Date().toISOString(),
        state: { candidates: [] },
      },
    });

    useJobStore.getState().updateJobStateFromSocket({
      current_stage: "screening",
      state: { scored_candidates: [{ candidate_id: "c1" }] },
    });

    const job = useJobStore.getState().currentJob;
    expect(job?.current_stage).toBe("screening");
    expect(job?.state).toMatchObject({
      candidates: [],
      scored_candidates: [{ candidate_id: "c1" }],
    });
  });
});
