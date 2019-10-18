import { VmsService } from '../all-vms/vms.service';
import { Component, OnInit } from '@angular/core';
import { map } from 'rxjs/operators';
import { ActivatedRoute, ParamMap } from '@angular/router';
import { Router } from '@angular/router';


@Component({
  selector: 'vdi-vm-details',
  templateUrl: './vm-details.component.html',
  styleUrls: ['./vm-details.component.scss']
})


export class VmDetailsComponent implements OnInit {

  public vm = {};

  public collectionDetails = [
    {
      title: 'Название',
      property: 'name',
      type: 'string'
    }
  ];

  public idVm: string;
  public menuActive: string = 'info';
  public host: boolean = false;

  constructor(private activatedRoute: ActivatedRoute,
              private service: VmsService,
              private router: Router) { }

  ngOnInit() {
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      this.idVm = param.get('id') as string;
      this.getVM();
    });
  }

  public getVM() {
    this.host = false;
    this.service.getVm(this.idVm).valueChanges.pipe(map(data => data.data.vm))
      .subscribe((data) => {
        this.vm = data;
        this.host = true;
      },
      () => {
        this.host = true;
      });
  }

  public close() {
    this.router.navigate(['resourses/vms']);
  }

  public routeTo(route: string): void {
    if (route === 'info') {
      this.menuActive = 'info';
    }
  }
}
