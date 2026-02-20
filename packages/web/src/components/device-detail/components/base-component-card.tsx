import type { ReactNode } from "react";

import { ComponentActions } from "../component-actions";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { Component } from "@/types/api";

interface BaseComponentCardProps {
  component: Component;
  deviceIp: string;
  borderColor: string;
  icon?: ReactNode;
  title: string;
  description?: string;
  badge?: {
    label: string;
    variant: "default" | "secondary" | "outline" | "destructive";
  };
  children: ReactNode;
}

export function BaseComponentCard({
  component,
  deviceIp,
  borderColor,
  icon,
  title,
  description,
  badge,
  children,
}: BaseComponentCardProps) {
  return (
    <Card className={`border-l-4 ${borderColor} h-full`}>
      <CardHeader className="pb-3">
        <CardTitle
          className={`flex items-center text-base${badge ? " justify-between" : " space-x-2"}`}
        >
          {icon ? (
            <div className="flex items-center space-x-2">
              {icon}
              <span>{title}</span>
            </div>
          ) : (
            <span>{title}</span>
          )}
          {badge && <Badge variant={badge.variant}>{badge.label}</Badge>}
        </CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent className="pt-0 flex-1 flex flex-col gap-6">
        {children}
        <div className="mt-auto pt-4 border-t">
          <ComponentActions component={component} deviceIp={deviceIp} />
        </div>
      </CardContent>
    </Card>
  );
}
