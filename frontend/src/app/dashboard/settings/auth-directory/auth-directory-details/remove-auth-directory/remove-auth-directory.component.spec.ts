import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { RemoveAuthenticationDirectoryComponent } from './remove-auth-directory.component';

describe('AddControllerComponent', () => {
  let component: RemoveAuthenticationDirectoryComponent;
  let fixture: ComponentFixture<RemoveAuthenticationDirectoryComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [RemoveAuthenticationDirectoryComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(RemoveAuthenticationDirectoryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
