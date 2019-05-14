import { Component, OnInit } from '@angular/core';
import { DatapoolsService } from './datapools.service';
import { map } from 'rxjs/operators';
import { ActivatedRoute, ParamMap, Router } from '@angular/router';

@Component({
  selector: 'vdi-datapools',
  templateUrl: './datapools.component.html',
  styleUrls: ['./datapools.component.scss']
})


export class DatapoolsComponent implements OnInit {

  public infoTemplates: [];
  public collection: object[] = [];
  public datapools: {};
  private id_cluster:string;

  public crumbs: object[] = [
    {
      title: 'Ресурсы',
      icon: 'database'
    },
    {
      title: 'Кластеры',
      icon: 'building',
      route: 'resourses/clusters'
    }
  ];

  public spinner:boolean = true;

  constructor(private service: DatapoolsService,private activatedRoute: ActivatedRoute,private router: Router){}

  ngOnInit() {
    this.collectionAction();

    // this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
    //   this.id_cluster = param.get('id') as string;
    //   console.log(param);
    //   this.getDatapools(this.id_cluster);

    //   this.crumbs.push(
    //     {
    //       title: 'Серверы',
    //       icon: 'server',
    //       route: `resourses/clusters/${this.id_cluster}/nodes`
    //     }
    //   );

    // });
  }

  // private getDatapools(id_cluster) {
  //   this.service.getAllDatapools(id_cluster).valueChanges.pipe(map(data => data.data.datapools))
  //     .subscribe( (data) => {
  //       this.datapools = data;
  //       this.spinner = false;
  //     },
  //     (error)=> {
  //       this.spinner = false;
  //     });
  // }

  public collectionAction(): void {
    this.collection = [
      {
        title: 'Название',
        property: 'verbose_name'
      },
      {
        title: 'Локация',
        property: "datacenter_name"
      },
      {
        title: 'IP-адрес',
        property: 'management_ip'
      },
      {
        title: 'CPU',
        property: 'cpu_count'
      },
      {
        title: 'RAM',
        property: 'memory_count'
      },
      {
        title: 'Статус',
        property: 'status'
      }
    ];
  }
}
