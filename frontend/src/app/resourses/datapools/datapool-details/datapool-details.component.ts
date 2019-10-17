import { DatapoolsService } from './../all-datapools/datapools.service';
import { Component, OnInit } from '@angular/core';
import { map } from 'rxjs/operators';
import { ActivatedRoute, ParamMap } from '@angular/router';
import { Router } from '@angular/router';


@Component({
  selector: 'vdi-datapool-details',
  templateUrl: './datapool-details.component.html',
  styleUrls: ['./datapool-details.component.scss']
})


export class DatapoolDetailsComponent implements OnInit {

  public datapool = {};

  public collectionDetails = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start',
      type: 'string',
      icon: 'folder-open'
    },
    {
      title: 'Тип',
      property: 'type',
      type: 'string'
    },
    {
      title: 'Диски',
      property: 'vdisk_count',
      type: 'string'
    },
    {
      title: 'Образы',
      property: 'iso_count',
      type: 'string'
    },
    {
      title: 'Файлы',
      property: 'file_count',
      type: 'string'
    },
    {
      title: 'Свободно (Мб)',
      property: 'free_space',
      type: 'string'
    },
    {
      title: 'Занято (Мб)',
      property: 'used_space',
      type: 'string'
    }
  ];

  public idDatapool: string;
  public menuActive: string = 'info';
  public host: boolean = false;

  constructor(private activatedRoute: ActivatedRoute,
              private service: DatapoolsService,
              private router: Router) { }

  ngOnInit() {
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      this.idDatapool = param.get('id') as string;
      this.getDatapool();
    });
  }

  public getDatapool() {
    this.host = false;
    this.service.getDatapool(this.idDatapool).valueChanges.pipe(map(data => data.data.datapool))
      .subscribe((data) => {
        this.datapool = data;
        this.host = true;
      },
        () => {
          this.host = true;
        });
  }

  public close() {
    this.router.navigate(['resourses/datapools']);
  }

  public routeTo(route: string): void {
    if (route === 'info') {
      this.menuActive = 'info';
    }
  }
}
