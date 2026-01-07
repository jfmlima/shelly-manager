import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Plus, Trash2, Shield, Loader2, Globe } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { credentialsApi, handleApiError } from "@/lib/api";
import type { Credential, CredentialCreateRequest } from "@/types/api";

interface CredentialsManagerProps {
  credentials: Credential[];
  isLoading: boolean;
}

export function CredentialsManager({
  credentials,
  isLoading,
}: CredentialsManagerProps) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [isOpen, setIsOpen] = useState(false);
  const [newCred, setNewCred] = useState<CredentialCreateRequest>({
    mac: "",
    username: "admin",
    password: "",
  });

  const setMutation = useMutation({
    mutationFn: credentialsApi.setCredential,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["credentials"] });
      toast.success(t("common.success"));
      setIsOpen(false);
      setNewCred({ mac: "", username: "admin", password: "" });
    },
    onError: (error) => {
      toast.error(handleApiError(error));
    },
  });

  const deleteMutation = useMutation({
    mutationFn: credentialsApi.deleteCredential,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["credentials"] });
      toast.success(t("common.success"));
    },
    onError: (error) => {
      toast.error(handleApiError(error));
    },
  });

  const handleAdd = () => {
    if (!newCred.mac || !newCred.password) {
      toast.error("MAC address and password are required");
      return;
    }
    // Ensure MAC is uppercase
    const mac = newCred.mac.trim().toUpperCase();
    setMutation.mutate({ ...newCred, mac });
  };

  const handleSetGlobal = () => {
    if (!newCred.password) {
      toast.error("Password is required for global fallback");
      return;
    }
    setMutation.mutate({ ...newCred, mac: "*" });
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold flex items-center gap-2">
          <Shield className="h-4 w-4 text-primary" />
          {t("dashboard.scanForm.credentials.title")}
        </h4>
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
          <DialogTrigger asChild>
            <Button variant="outline" size="sm" className="h-8 gap-2">
              <Plus className="h-3.5 w-3.5" />
              {t("dashboard.scanForm.credentials.add")}
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>
                {t("dashboard.scanForm.credentials.add")}
              </DialogTitle>
              <DialogDescription>
                Add credentials for a specific device or as a global fallback.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="mac">
                  {t("dashboard.scanForm.credentials.mac")}
                </Label>
                <Input
                  id="mac"
                  placeholder={t(
                    "dashboard.scanForm.credentials.placeholderMac",
                  )}
                  value={newCred.mac}
                  onChange={(e) =>
                    setNewCred({ ...newCred, mac: e.target.value })
                  }
                />
                <p className="text-xs text-muted-foreground flex items-center gap-1">
                  <Globe className="h-3 w-3" />
                  {t("dashboard.scanForm.credentials.globalLabel")}
                </p>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="username">
                  {t("dashboard.scanForm.credentials.username")}
                </Label>
                <Input
                  id="username"
                  placeholder={t(
                    "dashboard.scanForm.credentials.placeholderUsername",
                  )}
                  value={newCred.username}
                  onChange={(e) =>
                    setNewCred({ ...newCred, username: e.target.value })
                  }
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="password">
                  {t("dashboard.scanForm.credentials.password")}
                </Label>
                <Input
                  id="password"
                  type="password"
                  placeholder={t(
                    "dashboard.scanForm.credentials.placeholderPassword",
                  )}
                  value={newCred.password}
                  onChange={(e) =>
                    setNewCred({ ...newCred, password: e.target.value })
                  }
                />
              </div>
            </div>
            <DialogFooter className="gap-2 sm:gap-0">
              <Button
                variant="secondary"
                onClick={handleSetGlobal}
                disabled={setMutation.isPending}
              >
                {t("dashboard.scanForm.credentials.global")}
              </Button>
              <Button onClick={handleAdd} disabled={setMutation.isPending}>
                {setMutation.isPending && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                {t("common.save")}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[200px]">
                {t("dashboard.scanForm.credentials.mac")}
              </TableHead>
              <TableHead>
                {t("dashboard.scanForm.credentials.username")}
              </TableHead>
              <TableHead className="text-right">{t("common.delete")}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={3} className="h-24 text-center">
                  <div className="flex items-center justify-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    {t("common.loading")}
                  </div>
                </TableCell>
              </TableRow>
            ) : credentials.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={3}
                  className="h-24 text-center text-muted-foreground"
                >
                  {t("dashboard.scanForm.credentials.noCredentials")}
                </TableCell>
              </TableRow>
            ) : (
              credentials.map((cred) => (
                <TableRow key={cred.mac}>
                  <TableCell className="font-mono text-xs">
                    {cred.mac === "*" ? (
                      <span className="flex items-center gap-1 text-primary font-semibold">
                        <Globe className="h-3 w-3" />
                        {t("dashboard.scanForm.credentials.global")}
                      </span>
                    ) : (
                      cred.mac.toUpperCase()
                    )}
                  </TableCell>
                  <TableCell>{cred.username}</TableCell>
                  <TableCell className="text-right">
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-destructive hover:text-destructive hover:bg-destructive/10"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        deleteMutation.mutate(cred.mac);
                      }}
                      disabled={deleteMutation.isPending}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
