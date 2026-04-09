import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { AuthProvider, useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";

const pushMock = jest.fn();
const replaceMock = jest.fn();
const pathnameState = { value: "/dashboard" };

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, replace: replaceMock }),
  usePathname: () => pathnameState.value,
}));

jest.mock("@/lib/api", () => ({
  api: {
    me: jest.fn(),
    logout: jest.fn(),
  },
}));

function Consumer() {
  const { user, loading } = useAuth();
  if (loading) return <div data-testid="loading">loading</div>;
  return <div data-testid="user-email">{user?.email ?? "none"}</div>;
}

describe("AuthProvider", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    sessionStorage.clear();
    pathnameState.value = "/dashboard";
  });

  it("loads user via /me and sets context", async () => {
    (api.me as jest.Mock).mockResolvedValue({
      id: 1,
      email: "hr@prohr.ai",
      full_name: "HR",
      role: "hr_manager",
    });

    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("user-email")).toHaveTextContent("hr@prohr.ai");
    });
    expect(pushMock).not.toHaveBeenCalled();
  });

  it("redirects to landing when /me fails on protected route", async () => {
    (api.me as jest.Mock).mockRejectedValue(new Error("unauthorized"));

    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith("/");
    });
    expect(screen.getByTestId("user-email")).toHaveTextContent("none");
  });
});
