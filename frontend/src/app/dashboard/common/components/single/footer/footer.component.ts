import { Component, OnInit } from '@angular/core';
import { FooterService } from './footer.service';

@Component({
  selector: 'vdi-footer',
  templateUrl: './footer.component.html',
  styleUrls: ['./footer.component.scss'],
  providers: [ FooterService ]
})
export class FooterComponent implements OnInit {

  info: any = {};
  license: any = {};

  constructor(private service: FooterService) { }

  ngOnInit() {
    this.service.getInfo().subscribe((res) => {
      this.info = res.data;
    });

    this.service.getLicence().subscribe((res) => {
      this.license = res.data;
    });
  }

}
