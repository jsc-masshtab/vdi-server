import { VmsService } from '../all-vms/vms.service';
import { Component, OnInit } from '@angular/core';
import { map } from 'rxjs/operators';
import { ActivatedRoute, ParamMap } from '@angular/router';
import { Router } from '@angular/router';

interface ICollection {
  [index: string]: string;
}

@Component({
  selector: 'vdi-vm-details',
  templateUrl: './vm-details.component.html',
  styleUrls: ['./vm-details.component.scss']
})


export class VmDetailsComponent implements OnInit {

  public vm: ICollection = {};

  public collectionDetails = [
    {
      title: 'Название',
      property: 'verbose_name',
      class: 'name-start',
      icon: 'desktop',
      type: 'string'
    },
    {
      title: 'Шаблон',
      property: 'template',
      property_lv2: 'verbose_name'
    },
    {
      title: 'Контроллер',
      property: 'controller',
      property_lv2: 'address'
    },
    {
      title: 'Пользователь',
      property: 'user',
      property_lv2: 'username'
    }
  ];

  public idVm: string;
  public menuActive: string = 'info';
  public host: boolean = false;
  private address: string;

  constructor(private activatedRoute: ActivatedRoute,
              private service: VmsService,
              private router: Router) { }

  ngOnInit() {
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      this.idVm = param.get('id') as string;
      this.address = param.get('address');
      this.getVM();
    });
  }

  public getVM() {
    this.host = false;
    this.service.getVm(this.idVm, this.address).valueChanges.pipe(map(data => data.data.vm))
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