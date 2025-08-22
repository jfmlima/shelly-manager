import {
  UpdateActionConfig,
  RebootActionConfig,
  FactoryResetConfig,
  ExportConfigConfig,
  ApplyConfigConfig,
} from "./action-configurations";
import type { ActionConfigurationProps } from "../types";

export function ActionConfiguration({
  selectedAction,
  updateChannel,
  onUpdateChannelChange,
  confirmFactoryReset,
  onConfirmFactoryResetChange,
  selectedComponentTypes,
  onSelectedComponentTypesChange,
  selectedComponentType,
  onSelectedComponentTypeChange,
  configurationJson,
  onConfigurationJsonChange,
  configError,
  onExecute,
  onCancel,
}: ActionConfigurationProps) {
  switch (selectedAction) {
    case "update":
      return (
        <UpdateActionConfig
          updateChannel={updateChannel}
          onUpdateChannelChange={onUpdateChannelChange}
          onExecute={onExecute}
          onCancel={onCancel}
        />
      );

    case "reboot":
      return <RebootActionConfig onExecute={onExecute} onCancel={onCancel} />;

    case "factory_reset":
      return (
        <FactoryResetConfig
          confirmFactoryReset={confirmFactoryReset}
          onConfirmFactoryResetChange={onConfirmFactoryResetChange}
          onExecute={onExecute}
          onCancel={onCancel}
        />
      );

    case "export_config":
      return (
        <ExportConfigConfig
          selectedComponentTypes={selectedComponentTypes}
          onSelectedComponentTypesChange={onSelectedComponentTypesChange}
          onExecute={onExecute}
          onCancel={onCancel}
        />
      );

    case "apply_config":
      return (
        <ApplyConfigConfig
          selectedComponentType={selectedComponentType}
          onSelectedComponentTypeChange={onSelectedComponentTypeChange}
          configurationJson={configurationJson}
          onConfigurationJsonChange={onConfigurationJsonChange}
          configError={configError}
          onExecute={onExecute}
          onCancel={onCancel}
        />
      );

    default:
      return null;
  }
}
