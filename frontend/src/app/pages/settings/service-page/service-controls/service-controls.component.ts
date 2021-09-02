import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';

import { ActionType, IEventData } from '../service-page.component';
import { IQueryService, Status } from '../service-page.mapper';


@Component({
  selector: 'vdi-service-controls',
  templateUrl: './service-controls.component.html',
  styleUrls: ['./service-controls.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ServiceControlsComponent{

  @Input() service: IQueryService;
  @Output() clickControls: EventEmitter<IEventData> = new EventEmitter<IEventData>();

  public get isRunning(): boolean  {

    return this.service.status === Status.Running
  }

  public get isExited(): boolean  {

    return this.service.status === Status.Exited
  }

  public restart(): void {
    this.clickControls.emit({
      service: this.service,
      actionType: ActionType.Restart
    });
  }

  public run(): void {
    this.clickControls.emit({
      service: this.service,
      actionType: ActionType.Start
    });

  }

  public stop(): void {
    this.clickControls.emit({
      service: this.service,
      actionType: ActionType.Stop
    });
  }
}
