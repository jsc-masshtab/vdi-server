import { Component, OnInit } from '@angular/core';
import { ClustersService } from './clusters.service';
import { map } from 'rxjs/operators';
import { Router } from '@angular/router';

@Component({
  selector: 'vdi-clusters',
  templateUrl: './clusters.component.html',
  styleUrls: ['./clusters.component.scss']
})


export class ClustersComponent implements OnInit {

  public clusters: object[] = [];
  public collection: object[] = [
    {
      title: 'Название',
      property: 'verbose_name'
    },
    {
      title: 'Серверы',
      property: "nodes_count"
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
  public crumbs: object[] = [
    {
      title: 'Ресурсы',
      icon: 'database'
    }
  ];

  public spinner:boolean = false;

  constructor(private service: ClustersService,private router: Router){}

  ngOnInit() {
    this.getAllClusters();
  }

  private getAllClusters() {
    this.spinner = true;
    this.service.getAllClusters().valueChanges.pipe(map(data => data.data.clusters))
      .subscribe( (data) => {
        this.clusters = data;
        console.log(this.clusters,'dkdkdk');
        this.crumbs.push({
            title: 'Кластеры',
            icon: 'building'
        });
        this.spinner = false;
      },
      (error)=> {
        this.spinner = false;
      });
  }

  public routeTo(event): void {
    this.router.navigate([`resourses/clusters/${event.id}`]);
  }


}
