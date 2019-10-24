
import { WaitService } from './../../../common/components/single/wait/wait.service';
import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { DatapoolsService } from './datapools.service';
import { map } from 'rxjs/operators';
import { Router } from '@angular/router';
import { DetailsMove } from 'src/app/common/classes/details-move';


@Component({
  selector: 'vdi-datapools',
  templateUrl: './datapools.component.html',
  styleUrls: ['./datapools.component.scss']
})


export class DatapoolsComponent extends DetailsMove implements OnInit {

  public datapools: object[] = [];
  public collection: object[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start',
      type: 'string',
      icon: 'folder-open',
      reverse_sort: true
    },
    {
      title: 'Тип',
      property: 'type',
      type: 'string',
      reverse_sort: true
    },
    {
      title: 'Диски',
      property: 'vdisk_count',
      type: 'string',
      reverse_sort: true
    },
    {
      title: 'Образы',
      property: 'iso_count',
      type: 'string',
      reverse_sort: true
    },
    {
      title: 'Файлы',
      property: 'file_count',
      type: 'string',
      reverse_sort: true
    },
    {
      title: 'Свободно (Мб)',
      property: 'free_space',
      type: 'string',
      reverse_sort: true
    },
    {
      title: 'Занято (Мб)',
      property: 'used_space',
      type: 'string',
      reverse_sort: true
    },
    {
      title: 'Статус',
      property: 'status',
      reverse_sort: true
    }
  ];


  constructor(private service: DatapoolsService, private waitService: WaitService,  private router: Router) {
    super();
  }

  @ViewChild('view') view: ElementRef;

  ngOnInit() {
    this.getDatapools();
  }

  public getDatapools() {
    this.waitService.setWait(true);
    this.service.getAllDatapools().valueChanges.pipe(map(data => data.data.controllers))
      .subscribe( (data) => {
        let arrDatapools: [][] = [];
        this.datapools = [];
        arrDatapools = data.map(controller => controller.datapools);

        arrDatapools.forEach((arr: []) => {
            arr.forEach((obj: {}) => {
              this.datapools.push(obj);
            });
        });
        this.waitService.setWait(false);
      });
  }

  public routeTo(event): void {
    this.router.navigate([`resourses/datapools/${event.id}`]);
  }

  public onResize(): void {
    super.onResize(this.view);
  }

  public componentActivate(): void {
    super.componentActivate(this.view);
  }

  public componentDeactivate(): void {
    super.componentDeactivate();
  }

}
