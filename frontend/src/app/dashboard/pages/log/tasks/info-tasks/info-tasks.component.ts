import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialog } from '@angular/material/dialog';
import { TasksService } from '../all-tasks/tasks.service';
import { YesNoFormComponent } from 'src/app/dashboard/common/forms-dinamic/yes-no-form/yes-no-form.component';



@Component({
  selector: 'vdi-info-task',
  templateUrl: './info-tasks.component.html',
  styleUrls: ['./info-tasks.component.scss']
})
export class InfoTaskComponent {

  task: any;

  public collection: any[] = [
    {
      title: 'Задача',
      property: 'message',
      type: 'string'
    },
    {
      title: 'Тип',
      property: 'task_type',
      type: 'task_type',
    },
    {
      title: 'Статус',
      property: 'status',
      type: 'string',
    },
    {
      title: 'Время создания',
      property: 'started',
      type: 'time'
    },
    {
      title: 'Время завершения',
      property: 'finished',
      type: 'time'
    },
    {
      title: 'Продолжительность',
      property: 'duration',
      type: 'string'
    }
  ];

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    private service: TasksService,
    public dialog: MatDialog
  ) {
    this.task = data.task;
  }

  public cancelTask() {
    this.dialog.open(YesNoFormComponent, {
      disableClose: true,
      width: '500px',
      data: {
        form: {
          header: 'Подтверждение действия',
          question: 'Отменить задачу?',
          button: 'Выполнить'
        },
        request: {
          service: this.service,
          action: 'cancelTask',
          body: {
            task: this.task.id
          }
        }
      }
    });
  }
}
