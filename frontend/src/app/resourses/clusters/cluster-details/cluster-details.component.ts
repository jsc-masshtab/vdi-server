import { Component, OnInit } from '@angular/core';
import { ClustersService } from './cluster-details.service';
import { map } from 'rxjs/operators';
import { ActivatedRoute, ParamMap, Router } from '@angular/router';

@Component({
  selector: 'vdi-cluster-details',
  templateUrl: './cluster-details.component.html',
  styleUrls: ['./cluster-details.component.scss']
})


export class ClusterDetailsComponent implements OnInit {

  public clusters: [];
  public collection: object[] = [];
  public cluster_id:string;
  public cluster_name:string;
  public crumbs: object[] = [
    {
      title: 'Ресурсы',
      icon: 'database'
    },
    {
      title: 'Кластеры',
      icon: 'building',
      //route: 'resourses/clusters'
    }
  ];

  public spinner:boolean = true;

  constructor(private activatedRoute: ActivatedRoute,private router: Router){}

  ngOnInit() {
   
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      console.log(param);
      this.cluster_id = param.get('id') as string;
    });
  }

  // private getAllClusters() {
  //   this.service.getAllClusters().valueChanges.pipe(map(data => data.data.clusters))
  //     .subscribe( (data) => {
  //       this.clusters = data;
  //       this.spinner = false;
  //     },
  //     (error)=> {
  //       this.spinner = false;
  //     });
  // }

  // public collectionAction(): void {
  //   this.collection = [
  //     {
  //       title: 'Название',
  //       property: 'verbose_name'
  //     },
  //     {
  //       title: 'Серверы',
  //       property: "nodes_count"
       
  //     },
  //     {
  //       title: 'CPU',
  //       property: 'cpu_count'
  //     },
  //     {
  //       title: 'RAM',
  //       property: 'memory_count'
  //     },
  //     {
  //       title: 'Статус',
  //       property: 'status'
  //     }
  //   ];
  // }

  // public getInfoCluster(event): void {
  //   this.cluster_id = event.id;
  //   this.cluster_name = event.verbose_name;
  //   console.log(event.verbose_name);
  //  // this.router.navigate([`resourses/clusters/${event.id}/nodes`]);
  // }


}
